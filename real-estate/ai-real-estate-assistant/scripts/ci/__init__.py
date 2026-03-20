# Compatibility shim for renamed scripts
# Re-exports modules from their new locations

# Import docker.compose_smoke from scripts.docker
from scripts.docker.compose_smoke import (
    SmokeConfig,
    build_compose_base_command,
    build_compose_down_command,
    build_compose_up_command,
    get_default_api_access_key_from_env,
    http_get_status,
    main as compose_main,
    parse_args,
    wait_for_http_ok,
)

# Re-export with old names for backward compatibility
compose_smoke_SmokeConfig = SmokeConfig
compose_smoke_build_compose_base_command = build_compose_base_command
compose_smoke_build_compose_down_command = build_compose_down_command
compose_smoke_build_compose_up_command = build_compose_up_command
compose_smoke_get_default_api_access_key_from_env = get_default_api_access_key_from_env
compose_smoke_http_get_status = http_get_status
compose_smoke_main = compose_main
compose_smoke_parse_args = parse_args
compose_smoke_wait_for_http_ok = wait_for_http_ok
