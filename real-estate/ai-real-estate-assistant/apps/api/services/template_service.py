"""Template service for document rendering and PDF generation.

This service handles:
1. Jinja2 template rendering with variable substitution
2. HTML to PDF conversion
3. Template validation
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, TemplateSyntaxError, UndefinedError
from jinja2.exceptions import TemplateError

# PDF generation is more lightweight than ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

logger = logging.getLogger(__name__)

# Try to import weasyprint for better PDF generation
try:
    from weasyprint import CSS, HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not available, falling back to reportlab for PDF generation")


class TemplateService:
    """Service for rendering document templates with variable substitution."""

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        use_weasyprint: bool = True,
    ):
        """
        Initialize template service.

        Args:
            templates_dir: Directory containing default templates
            use_weasyprint: Whether to use WeasyPrint (better PDF) or ReportLab
        """
        self.templates_dir = templates_dir
        self.use_weasyprint = use_weasyprint and WEASYPRINT_AVAILABLE
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(
        self,
        template_content: str,
        variables: dict[str, Any],
    ) -> str:
        """
        Render a Jinja2 template with the provided variables.

        Args:
            template_content: Jinja2 template content (HTML)
            variables: Dictionary of variables to substitute

        Returns:
            Rendered HTML string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            UndefinedError: If required variables are missing
        """
        try:
            template = self.jinja_env.from_string(template_content)
            return template.render(**variables)
        except (TemplateSyntaxError, UndefinedError):
            logger.exception("Template rendering error")
            raise

    def validate_template(
        self,
        template_content: str,
        required_variables: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Validate a template for syntax errors and missing variables.

        Args:
            template_content: Jinja2 template content
            required_variables: List of variable names that must be present

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Check syntax
        try:
            template = self.jinja_env.from_string(template_content)
        except TemplateSyntaxError as e:
            errors.append(f"Template syntax error: {e}")
            return errors

        # Extract variables used in template
        vars_used = set()
        for node in template.environment.parse(template_content).body:
            for found_node in template.environment.parse(template_content).find(node):
                if isinstance(found_node, tuple) and found_node[0] == "var":
                    vars_used.add(found_node[1].name)

        # Check required variables
        if required_variables:
            missing = set(required_variables) - vars_used
            if missing:
                errors.append(f"Missing required variables: {', '.join(missing)}")

        return errors

    def extract_variables(self, template_content: str) -> list[str]:
        """
        Extract all variable names used in a template.

        Args:
            template_content: Jinja2 template content

        Returns:
            List of variable names used in the template
        """
        try:
            template = self.jinja_env.from_string(template_content)
            vars_used = set()
            ast = template.environment.parse(template_content)

            for node in ast.find_all(ast.body):
                if hasattr(node, "name") and isinstance(node.name, str):
                    vars_used.add(node.name)

            return sorted(vars_used)
        except TemplateError:
            logger.exception("Error extracting variables from template")
            return []

    def html_to_pdf_weasyprint(
        self,
        html_content: str,
        output_path: Path,
        page_size: str = "A4",
        margin_mm: int = 20,
    ) -> bool:
        """
        Convert HTML to PDF using WeasyPrint (better CSS support).

        Args:
            html_content: HTML content to convert
            output_path: Path to save PDF
            page_size: Page size (A4, Letter, etc.)
            margin_mm: Margin in millimeters

        Returns:
            True if successful
        """
        if not WEASYPRINT_AVAILABLE:
            logger.warning("WeasyPrint not available, cannot generate PDF")
            return False

        try:
            css = CSS(
                string=f"""
                @page {{
                    size: {page_size};
                    margin: {margin_mm}mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f5f5f5;
                }}
            """
            )

            html = HTML(string=html_content)
            html.write_pdf(output_path, stylesheets=[css])
            return True
        except Exception:
            logger.exception("Error generating PDF with WeasyPrint")
            return False

    def html_to_pdf_reportlab(
        self,
        html_content: str,
        output_path: Path,
        title: Optional[str] = None,
    ) -> bool:
        """
        Convert HTML to PDF using ReportLab (fallback).

        Note: ReportLab doesn't support full HTML/CSS. Use for simple documents only.

        Args:
            html_content: HTML content to convert
            output_path: Path to save PDF
            title: Optional document title

        Returns:
            True if successful
        """
        try:
            # Strip HTML tags for basic text extraction
            text = re.sub(r"<[^>]+>", "", html_content)
            text = re.sub(r"\s+", " ", text).strip()

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                leftMargin=50,
                rightMargin=50,
                topMargin=50,
                bottomMargin=50,
            )

            styles = getSampleStyleSheet()
            story = []

            if title:
                story.append(Paragraph(title, styles["Title"]))
                story.append(Spacer(1, 20))

            # Split into paragraphs
            for paragraph in text.split("\n\n"):
                if paragraph.strip():
                    story.append(Paragraph(paragraph.strip(), styles["Normal"]))
                    story.append(Spacer(1, 10))

            doc.build(story)
            return True
        except Exception:
            logger.exception("Error generating PDF with ReportLab")
            return False

    def generate_pdf(
        self,
        template_content: str,
        variables: dict[str, Any],
        output_path: Path,
        title: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Render template and generate PDF.

        Args:
            template_content: Jinja2 template content
            variables: Variables to substitute
            output_path: Path to save PDF
            title: Optional document title

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Render HTML
            html = self.render_template(template_content, variables)

            # Convert to PDF
            if self.use_weasyprint:
                success = self.html_to_pdf_weasyprint(html, output_path)
            else:
                success = self.html_to_pdf_reportlab(html, output_path, title)

            if success:
                return True, ""
            return False, "PDF generation failed"
        except TemplateError as e:
            return False, f"Template error: {e}"
        except Exception as e:
            return False, f"Error generating PDF: {e}"

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for integrity verification."""
        return hashlib.sha256(content.encode()).hexdigest()


# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "documents"


# Global instance
_template_service: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """Get or create the global template service instance."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService(templates_dir=DEFAULT_TEMPLATES_DIR)
    return _template_service
