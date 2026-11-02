"""Safe Jinja rendering for reusable outreach templates."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape

from jinja2 import ChainableUndefined, Environment


PLAIN_ENVIRONMENT = Environment(undefined=ChainableUndefined, autoescape=False)
HTML_ENVIRONMENT = Environment(
    undefined=ChainableUndefined,
    autoescape=False,
)


def render_text(template_text: str, values: Mapping[str, object]) -> str:
    """Render a user-editable plain-text template without failing on omissions."""

    return PLAIN_ENVIRONMENT.from_string(template_text).render(**values).strip()


def render_html(template_text: str, values: Mapping[str, object]) -> str:
    """Render template content as simple, readable HTML.

    Existing HTML is preserved for advanced templates; ordinary lines become
    paragraphs and URLs in the rendered text are linked by the email builder.
    """

    rendered = HTML_ENVIRONMENT.from_string(template_text).render(**values).strip()
    if "<" in rendered and ">" in rendered:
        return rendered
    paragraphs = [escape(part.strip()).replace("\n", "<br>\n") for part in rendered.split("\n\n") if part.strip()]
    return "\n\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)


def validate_template_syntax(template_text: str) -> str | None:
    """Return a friendly syntax error, if any, without rendering the template."""

    try:
        PLAIN_ENVIRONMENT.parse(template_text)
    except Exception as exc:  # Jinja has multiple syntax exception subclasses.
        return str(exc)
    return None
