from typing import List

from fastapi import APIRouter, HTTPException, status

from ai.prompt_templates import (
    get_prompt_template_by_id,
    get_prompt_templates,
    render_prompt_template,
)
from api.models import (
    PromptTemplateApplyRequest,
    PromptTemplateApplyResponse,
    PromptTemplateInfo,
    PromptTemplateVariableInfo,
)

router = APIRouter()


@router.get("/prompt-templates", response_model=List[PromptTemplateInfo], tags=["Prompt Templates"])
async def list_prompt_templates() -> List[PromptTemplateInfo]:
    templates = []
    for tmpl in get_prompt_templates():
        templates.append(
            PromptTemplateInfo(
                id=tmpl.id,
                title=tmpl.title,
                category=tmpl.category,
                description=tmpl.description,
                template_text=tmpl.template_text,
                variables=[
                    PromptTemplateVariableInfo(
                        name=v.name,
                        description=v.description,
                        required=v.required,
                        example=v.example,
                    )
                    for v in tmpl.variables
                ],
            )
        )
    return templates


@router.post(
    "/prompt-templates/apply",
    response_model=PromptTemplateApplyResponse,
    tags=["Prompt Templates"],
)
async def apply_prompt_template(
    request: PromptTemplateApplyRequest,
) -> PromptTemplateApplyResponse:
    tmpl = get_prompt_template_by_id(request.template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        )

    try:
        rendered = render_prompt_template(tmpl, request.variables)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply prompt template: {str(e)}",
        ) from e

    return PromptTemplateApplyResponse(template_id=tmpl.id, rendered_text=rendered)
