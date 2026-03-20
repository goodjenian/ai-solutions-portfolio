"""Tests for the RBAC system (TASK-018)."""

from unittest.mock import MagicMock, patch

import pytest

from api.rbac import (
    ROLE_PERMISSIONS,
    Permission,
    RBACChecker,
    Role,
    UserContext,
    get_rbac_checker,
    require_admin,
    require_permission,
    require_role,
)


class TestRolePermissions:
    """Tests for role permissions mapping."""

    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        # Admin should have all defined permissions
        all_permissions = set(Permission)
        assert admin_perms == all_permissions

    def test_user_permissions(self):
        """Test that user role has appropriate permissions."""
        user_perms = ROLE_PERMISSIONS[Role.USER]
        # User should have standard permissions but not admin ones
        assert Permission.DATA_READ in user_perms
        assert Permission.FEATURE_SEARCH in user_perms
        assert Permission.ADMIN_MANAGE_USERS not in user_perms

    def test_read_only_permissions(self):
        """Test that read_only role has only read permissions."""
        ro_perms = ROLE_PERMISSIONS[Role.READ_ONLY]
        assert Permission.DATA_READ in ro_perms
        assert Permission.DATA_WRITE not in ro_perms
        assert Permission.DATA_DELETE not in ro_perms


class TestUserContext:
    """Tests for UserContext."""

    def test_create_user_context(self):
        """Test creating a user context."""
        context = UserContext(
            client_id="abc123",
            roles={Role.USER},
            permissions={Permission.DATA_READ, Permission.FEATURE_SEARCH},
            request_id="req-123",
        )
        assert context.client_id == "abc123"
        assert Role.USER in context.roles
        assert Permission.DATA_READ in context.permissions
        assert context.request_id == "req-123"


class TestRBACChecker:
    """Tests for RBACChecker."""

    def test_init_default_keys(self):
        """Test RBACChecker initialization with default keys."""
        with patch("config.settings.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_access_keys=["test_key"])

            checker = RBACChecker()

            # Default keys should be determined from key patterns
            # Since "test_key" doesn't match admin/readonly patterns,
            # it should be classified as a user key
            assert "test_key" in checker._user_keys

    def test_init_explicit_keys(self):
        """Test RBACChecker initialization with explicit keys."""
        checker = RBACChecker(
            admin_api_keys={"admin_key"},
            user_api_keys={"user_key"},
            read_only_api_keys={"readonly_key"},
        )

        assert "admin_key" in checker._admin_keys
        assert "user_key" in checker._user_keys
        assert "readonly_key" in checker._read_only_keys

    def test_get_roles_for_key_admin(self):
        """Test getting roles for admin API key."""
        checker = RBACChecker(admin_api_keys={"admin_key"})
        roles = checker._get_roles_for_key("admin_key")
        assert Role.ADMIN in roles

    def test_get_roles_for_key_user(self):
        """Test getting roles for user API key."""
        checker = RBACChecker(user_api_keys={"user_key"})
        roles = checker._get_roles_for_key("user_key")
        assert Role.USER in roles

    def test_get_roles_for_key_unknown(self):
        """Test getting roles for unknown API key defaults to API_CLIENT."""
        checker = RBACChecker()
        roles = checker._get_roles_for_key("unknown_key")
        assert Role.API_CLIENT in roles

    def test_get_permissions_for_roles(self):
        """Test getting permissions for a set of roles."""
        checker = RBACChecker()
        permissions = checker._get_permissions_for_roles({Role.USER, Role.READ_ONLY})
        # Should have union of permissions
        assert Permission.DATA_READ in permissions

    def test_get_user_context(self):
        """Test getting user context for API key."""
        checker = RBACChecker(user_api_keys={"user_key"})
        context = checker.get_user_context("user_key", request_id="req-123")

        assert context.client_id is not None  # Hashed
        assert Role.USER in context.roles or Role.API_CLIENT in context.roles
        assert context.request_id == "req-123"

    def test_check_role_success(self):
        """Test checking role when user has it."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.ADMIN},
            permissions=set(),
        )
        assert checker.check_role(context, Role.ADMIN) is True

    def test_check_role_failure(self):
        """Test checking role when user doesn't have it."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.READ_ONLY},
            permissions=set(),
        )
        assert checker.check_role(context, Role.ADMIN) is False

    def test_check_permission_success(self):
        """Test checking permission when user has it."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.USER},
            permissions={Permission.DATA_READ},
        )
        assert checker.check_permission(context, Permission.DATA_READ) is True

    def test_check_permission_failure(self):
        """Test checking permission when user doesn't have it."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.READ_ONLY},
            permissions={Permission.DATA_READ},
        )
        assert checker.check_permission(context, Permission.DATA_DELETE) is False

    def test_check_any_role(self):
        """Test checking if user has any of required roles."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.USER},
            permissions=set(),
        )
        assert checker.check_any_role(context, {Role.ADMIN, Role.USER}) is True
        assert checker.check_any_role(context, {Role.ADMIN, Role.READ_ONLY}) is False

    def test_check_all_roles(self):
        """Test checking if user has all required roles."""
        checker = RBACChecker()
        context = UserContext(
            client_id="test",
            roles={Role.USER},
            permissions=set(),
        )
        assert checker.check_all_roles(context, {Role.USER}) is True
        assert checker.check_all_roles(context, {Role.USER, Role.ADMIN}) is False


class TestDecorators:
    """Tests for RBAC decorators."""

    @pytest.mark.asyncio
    async def test_require_role_decorator(self):
        """Test require_role decorator."""
        checker = RBACChecker(user_api_keys={"user_key"})

        with patch("api.rbac.get_rbac_checker", return_value=checker):
            decorator = require_role(Role.USER)

            @decorator
            async def test_endpoint(request):
                return {"success": True}

            # Mock request with API key
            request = MagicMock()
            request.state.api_key = "user_key"
            request.state.request_id = "req-123"

            result = await test_endpoint(request)
            assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_require_role_decorator_unauthorized(self):
        """Test require_role decorator with insufficient role."""
        checker = RBACChecker(user_api_keys={"user_key"})

        with patch("api.rbac.get_rbac_checker", return_value=checker):
            decorator = require_role(Role.ADMIN)

            @decorator
            async def test_endpoint(request):
                return {"success": True}

            # Mock request with user key (not admin)
            request = MagicMock()
            request.state.api_key = "user_key"
            request.state.request_id = "req-123"

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(request)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_decorator(self):
        """Test require_permission decorator."""
        checker = RBACChecker(user_api_keys={"user_key"})

        with patch("api.rbac.get_rbac_checker", return_value=checker):
            decorator = require_permission(Permission.DATA_READ)

            @decorator
            async def test_endpoint(request):
                return {"success": True}

            request = MagicMock()
            request.state.api_key = "user_key"
            request.state.request_id = "req-123"

            result = await test_endpoint(request)
            assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_require_admin_decorator(self):
        """Test require_admin decorator."""
        checker = RBACChecker(admin_api_keys={"admin_key"})

        with patch("api.rbac.get_rbac_checker", return_value=checker):
            decorator = require_admin()

            @decorator
            async def test_endpoint(request):
                return {"success": True}

            request = MagicMock()
            request.state.api_key = "admin_key"
            request.state.request_id = "req-123"

            result = await test_endpoint(request)
            assert result == {"success": True}


class TestGlobalFunctions:
    """Tests for global RBAC functions."""

    def test_get_rbac_checker_singleton(self):
        """Test that get_rbac_checker returns singleton instance."""
        checker1 = get_rbac_checker()
        checker2 = get_rbac_checker()
        assert checker1 is checker2
