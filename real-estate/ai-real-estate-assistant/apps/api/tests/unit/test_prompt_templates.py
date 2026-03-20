import pytest

from ai.prompt_templates import (
    get_prompt_template_by_id,
    get_prompt_templates,
    render_prompt_template,
)


def test_templates_have_unique_ids():
    templates = get_prompt_templates()
    ids = [t.id for t in templates]
    assert ids
    assert len(ids) == len(set(ids))


def test_render_listing_description_success():
    tmpl = get_prompt_template_by_id("listing_description_v1")
    assert tmpl is not None

    rendered = render_prompt_template(
        tmpl,
        {
            "area": "Krakow, Kazimierz",
            "property_type": "apartment",
            "area_sqm": "55",
            "rooms": "2",
            "price": "650,000 PLN",
            "features": "balcony, elevator",
        },
    )

    assert "Krakow, Kazimierz" in rendered
    assert "{{" not in rendered
    assert "balcony" in rendered


def test_render_missing_required_variables_raises():
    tmpl = get_prompt_template_by_id("buyer_followup_email_v1")
    assert tmpl is not None

    with pytest.raises(ValueError, match="Missing required variables"):
        render_prompt_template(
            tmpl,
            {
                "buyer_name": "Alex",
                "agent_name": "Maria",
            },
        )


def test_render_unknown_variables_raises():
    tmpl = get_prompt_template_by_id("buyer_followup_email_v1")
    assert tmpl is not None

    with pytest.raises(ValueError, match="Unknown variables"):
        render_prompt_template(
            tmpl,
            {
                "property_address": "Main St 10",
                "buyer_name": "Alex",
                "agent_name": "Maria",
                "unexpected": "x",
            },
        )


def test_render_optional_variable_can_be_omitted():
    tmpl = get_prompt_template_by_id("viewing_request_email_v1")
    assert tmpl is not None

    rendered = render_prompt_template(
        tmpl,
        {
            "property_address": "Kazimierz, Krakow",
            "slot_1": "Wed 18:00",
            "slot_2": "Thu 12:30",
            "requester_name": "Alex",
        },
    )

    assert "Kazimierz, Krakow" in rendered
    assert "{{requester_phone}}" not in rendered
    assert "{{" not in rendered
