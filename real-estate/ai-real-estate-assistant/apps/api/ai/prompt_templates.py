from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PromptTemplateVariable:
    name: str
    description: str
    required: bool = True
    example: str | None = None


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    title: str
    category: str
    description: str
    template_text: str
    variables: tuple[PromptTemplateVariable, ...]


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def _extract_placeholders(text: str) -> set[str]:
    return {m.group(1) for m in _PLACEHOLDER_RE.finditer(text)}


def get_prompt_templates() -> list[PromptTemplate]:
    return list(_TEMPLATES)


def get_prompt_template_by_id(template_id: str) -> PromptTemplate | None:
    for tmpl in _TEMPLATES:
        if tmpl.id == template_id:
            return tmpl
    return None


def render_prompt_template(template: PromptTemplate, variables: Mapping[str, Any]) -> str:
    declared_vars = {v.name: v for v in template.variables}

    unknown_vars = sorted(set(variables.keys()) - set(declared_vars.keys()))
    if unknown_vars:
        raise ValueError(f"Unknown variables: {', '.join(unknown_vars)}")

    missing_required = [
        v.name
        for v in template.variables
        if v.required and not _is_non_empty_string(variables.get(v.name))
    ]
    if missing_required:
        raise ValueError(f"Missing required variables: {', '.join(missing_required)}")

    placeholders = _extract_placeholders(template.template_text)
    undeclared_placeholders = sorted(placeholders - set(declared_vars.keys()))
    if undeclared_placeholders:
        raise ValueError(
            f"Template contains undeclared placeholders: {', '.join(undeclared_placeholders)}"
        )

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = variables.get(name)
        if value is None:
            return ""
        return str(value).strip()

    rendered = _PLACEHOLDER_RE.sub(_replace, template.template_text)
    return _cleanup_rendered(rendered)


def _cleanup_rendered(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


_TEMPLATES: tuple[PromptTemplate, ...] = (
    PromptTemplate(
        id="listing_description_v1",
        title="Listing description (friendly)",
        category="listing_description",
        description="Generates a concise listing description with key highlights and a clear CTA.",
        template_text=(
            "Write a listing description for the property below.\n\n"
            "Property:\n"
            "- Address/Area: {{area}}\n"
            "- Type: {{property_type}}\n"
            "- Size: {{area_sqm}} m²\n"
            "- Rooms: {{rooms}}\n"
            "- Price: {{price}}\n"
            "- Key features: {{features}}\n\n"
            "Tone: friendly, clear, non-salesy.\n"
            "Constraints:\n"
            "- 120–180 words\n"
            "- Use short paragraphs\n"
            "- End with a call-to-action to schedule a viewing\n"
        ),
        variables=(
            PromptTemplateVariable(
                name="area",
                description="Neighborhood or area (e.g., 'Krakow, Kazimierz').",
                example="Krakow, Kazimierz",
            ),
            PromptTemplateVariable(
                name="property_type",
                description="Property type (e.g., apartment, house).",
                example="apartment",
            ),
            PromptTemplateVariable(
                name="area_sqm",
                description="Size in square meters.",
                example="55",
            ),
            PromptTemplateVariable(
                name="rooms",
                description="Number of rooms.",
                example="2",
            ),
            PromptTemplateVariable(
                name="price",
                description="Price with currency.",
                example="650,000 PLN",
            ),
            PromptTemplateVariable(
                name="features",
                description="Comma-separated key features (balcony, parking, etc.).",
                example="balcony, elevator, parking spot",
            ),
        ),
    ),
    PromptTemplate(
        id="buyer_followup_email_v1",
        title="Buyer follow-up email",
        category="email",
        description="Follow-up email after an inquiry with next steps and a short question set.",
        template_text=(
            "Subject: Quick follow-up on {{property_address}}\n\n"
            "Hi {{buyer_name}},\n\n"
            "Thanks for reaching out about {{property_address}}. "
            "I’d be happy to help.\n\n"
            "A few quick questions so I can tailor options:\n"
            "1) Your preferred move-in timeline?\n"
            "2) Must-haves (e.g., balcony, parking, elevator)?\n"
            "3) Target budget range?\n\n"
            "If you’d like, we can schedule a short viewing call or an in-person visit. "
            "What times work best for you this week?\n\n"
            "Best regards,\n"
            "{{agent_name}}\n"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_address",
                description="Property address or short reference name.",
                example="Main St 10, Warsaw",
            ),
            PromptTemplateVariable(
                name="buyer_name",
                description="Recipient name.",
                example="Alex",
            ),
            PromptTemplateVariable(
                name="agent_name",
                description="Sender name.",
                example="Maria Nowak",
            ),
        ),
    ),
    PromptTemplate(
        id="viewing_request_email_v1",
        title="Viewing request email",
        category="email",
        description="Email requesting a viewing with two time slots and required info.",
        template_text=(
            "Subject: Viewing request — {{property_address}}\n\n"
            "Hello,\n\n"
            "I’m interested in viewing {{property_address}}. "
            "Would either of these times work?\n"
            "- {{slot_1}}\n"
            "- {{slot_2}}\n\n"
            "If not, please suggest a couple of alternatives. "
            "Also, could you confirm any requirements (ID, deposit terms, etc.)?\n\n"
            "Thank you,\n"
            "{{requester_name}}\n"
            "{{requester_phone}}\n"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_address",
                description="Property address or listing reference.",
                example="Kazimierz, Krakow (2-bed)",
            ),
            PromptTemplateVariable(
                name="slot_1",
                description="First proposed time slot.",
                example="Wed 18:00",
            ),
            PromptTemplateVariable(
                name="slot_2",
                description="Second proposed time slot.",
                example="Thu 12:30",
            ),
            PromptTemplateVariable(
                name="requester_name",
                description="Your name.",
                example="Alex",
            ),
            PromptTemplateVariable(
                name="requester_phone",
                description="Phone number (optional).",
                required=False,
                example="+48 123 456 789",
            ),
        ),
    ),
    # TASK-023: AI Listing Generator Templates
    PromptTemplate(
        id="listing_description_v2_llm",
        title="Full property description generator",
        category="listing_description",
        description="Generates comprehensive property descriptions with customizable tone and language support.",
        template_text=(
            "You are a professional real estate copywriter. Write a compelling property description in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Tone: {{tone_description}}\n"
            "- Length: {{max_words}} words maximum\n"
            "- Include: key features, location benefits, and lifestyle appeal\n"
            "- End with: a clear call-to-action to schedule a viewing\n"
            "- Format: Use short paragraphs (2-3 sentences each) for readability\n"
            "- Avoid: overly salesy language, excessive punctuation, clichés\n\n"
            "Write the property description now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details as structured text or JSON.",
                example="2-bed apartment in Krakow, 55m², balcony, 450,000 PLN",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name (English, Polish, Spanish, etc.).",
                example="English",
            ),
            PromptTemplateVariable(
                name="tone_description",
                description="Tone description (professional, friendly, luxury).",
                example="Formal, trustworthy, business-oriented",
            ),
            PromptTemplateVariable(
                name="max_words",
                description="Maximum word count.",
                example="150",
            ),
        ),
    ),
    PromptTemplate(
        id="headline_generator_v1",
        title="Property headline generator",
        category="headline",
        description="Generates multiple catchy headlines for property listings.",
        template_text=(
            "You are a real estate marketing expert. Write {{count}} compelling listing headlines in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Style: {{style_description}}\n"
            "- Length: 40-80 characters per headline (ideal for listings)\n"
            "- Variety: Mix of benefit-focused, feature-focused, and curiosity-driven headlines\n"
            "- Format: Return as a numbered list\n\n"
            "Generate {{count}} unique headlines now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details as structured text or JSON.",
                example="Luxury penthouse in Warsaw, 3 bedrooms, panoramic view",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name.",
                example="English",
            ),
            PromptTemplateVariable(
                name="count",
                description="Number of headlines to generate.",
                example="5",
            ),
            PromptTemplateVariable(
                name="style_description",
                description="Headline style description.",
                example="Attention-grabbing, emotional, uses power words",
            ),
        ),
    ),
    PromptTemplate(
        id="social_media_facebook_v1",
        title="Facebook property post generator",
        category="social_media",
        description="Generates Facebook-optimized property posts with hashtags and emojis.",
        template_text=(
            "You are a social media expert for real estate. Create a Facebook post in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Tone: {{tone_description}}\n"
            "- Facebook-friendly: engaging opener, bullet points for features, community feel\n"
            "- Length: Maximum 500 characters\n"
            "- Hashtags: Include 3-5 relevant hashtags at the end\n"
            "- Emojis: {{emoji_instruction}}\n"
            "- Call-to-action: {{cta_instruction}}\n\n"
            "Generate the Facebook post now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details.",
                example="Cozy apartment in city center",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name.",
                example="English",
            ),
            PromptTemplateVariable(
                name="tone_description",
                description="Content tone description.",
                example="Energetic, attention-grabbing, interactive",
            ),
            PromptTemplateVariable(
                name="emoji_instruction",
                description="Whether to include emojis.",
                example="Include relevant emojis",
            ),
            PromptTemplateVariable(
                name="cta_instruction",
                description="Call-to-action instruction.",
                example="End with a clear call-to-action",
            ),
        ),
    ),
    PromptTemplate(
        id="social_media_instagram_v1",
        title="Instagram property post generator",
        category="social_media",
        description="Generates Instagram-optimized property captions with hashtags.",
        template_text=(
            "You are a social media expert for real estate. Create an Instagram caption in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Tone: {{tone_description}}\n"
            "- Instagram-style: visual hooks in text, line breaks for readability, aesthetic focus\n"
            "- Length: Maximum 1500 characters\n"
            "- Hashtags: Include 8-15 relevant hashtags at the end\n"
            "- Emojis: {{emoji_instruction}}\n"
            "- Call-to-action: {{cta_instruction}}\n\n"
            "Generate the Instagram caption now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details.",
                example="Modern studio with city views",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name.",
                example="English",
            ),
            PromptTemplateVariable(
                name="tone_description",
                description="Content tone description.",
                example="Energetic, attention-grabbing, interactive",
            ),
            PromptTemplateVariable(
                name="emoji_instruction",
                description="Whether to include emojis.",
                example="Include relevant emojis",
            ),
            PromptTemplateVariable(
                name="cta_instruction",
                description="Call-to-action instruction.",
                example="End with a clear call-to-action",
            ),
        ),
    ),
    PromptTemplate(
        id="social_media_linkedin_v1",
        title="LinkedIn property post generator",
        category="social_media",
        description="Generates LinkedIn-optimized property posts with professional tone.",
        template_text=(
            "You are a social media expert for real estate. Create a LinkedIn post in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Tone: {{tone_description}}\n"
            "- LinkedIn-appropriate: professional tone, industry insights, business value\n"
            "- Length: Maximum 2000 characters\n"
            "- Hashtags: Include 3-5 relevant hashtags at the end\n"
            "- Emojis: Minimal, professional use only - {{emoji_instruction}}\n"
            "- Call-to-action: {{cta_instruction}}\n\n"
            "Generate the LinkedIn post now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details.",
                example="Premium office space in business district",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name.",
                example="English",
            ),
            PromptTemplateVariable(
                name="tone_description",
                description="Content tone description.",
                example="Professional, business-oriented",
            ),
            PromptTemplateVariable(
                name="emoji_instruction",
                description="Whether to include emojis.",
                example="Minimal professional emojis",
            ),
            PromptTemplateVariable(
                name="cta_instruction",
                description="Call-to-action instruction.",
                example="End with a clear call-to-action",
            ),
        ),
    ),
    PromptTemplate(
        id="social_media_twitter_v1",
        title="Twitter/X property post generator",
        category="social_media",
        description="Generates Twitter-optimized property posts with character limit.",
        template_text=(
            "You are a social media expert for real estate. Create a Twitter/X post in {{language}}.\n\n"
            "Property Details:\n"
            "{{property_data}}\n\n"
            "Requirements:\n"
            "- Tone: {{tone_description}}\n"
            "- Twitter/X format: concise, punchy, one key highlight, space-saving\n"
            "- Length: Maximum 280 characters (strictly enforced)\n"
            "- Hashtags: Include 1-3 relevant hashtags at the end\n"
            "- Emojis: Minimal - {{emoji_instruction}}\n"
            "- Call-to-action: {{cta_instruction}}\n\n"
            "Generate the Twitter post now:"
        ),
        variables=(
            PromptTemplateVariable(
                name="property_data",
                description="Property details.",
                example="Charming apartment near park",
            ),
            PromptTemplateVariable(
                name="language",
                description="Output language name.",
                example="English",
            ),
            PromptTemplateVariable(
                name="tone_description",
                description="Content tone description.",
                example="Energetic, attention-grabbing",
            ),
            PromptTemplateVariable(
                name="emoji_instruction",
                description="Whether to include emojis.",
                example="Minimal emojis",
            ),
            PromptTemplateVariable(
                name="cta_instruction",
                description="Call-to-action instruction.",
                example="Include link in bio",
            ),
        ),
    ),
)

_TEMPLATE_IDS = [t.id for t in _TEMPLATES]
if len(_TEMPLATE_IDS) != len(set(_TEMPLATE_IDS)):
    raise RuntimeError("Duplicate prompt template IDs detected")
