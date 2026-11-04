"""Shared preview and delivery content, including the automatic profile footer."""

from html import unescape
import re
from collections.abc import Mapping

from services.template_service import render_html, render_text


PROFILE_LINKS = (
    ("LinkedIn", "linkedin_url"),
    ("GitHub", "github_url"),
    ("Portfolio", "portfolio_url"),
)


def _plain_html(html: str) -> str:
    # Preserve link destinations in the readable text alternative.
    html = re.sub(
        r'<a\b[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>',
        lambda match: f"{match[2]} ({match[1]})" if match[1] not in match[2] else match[2],
        html, flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(r"<br\s*/?>|</(?:p|div|li|h[1-6])>", "\n", html, flags=re.IGNORECASE)
    return unescape(re.sub(r"<[^>]+>", "", html)).strip()


def render_email_content(template: str, values: Mapping[str, object]) -> tuple[str, str]:
    """Add saved signature and missing profile links once, for every template."""
    body = render_text(template, values)
    is_html = bool(re.search(r"</?[a-zA-Z][^>]*>", body))
    plain = _plain_html(body) if is_html else body
    signature = str(values.get("signature") or "").strip()
    footer: list[str] = []
    if signature and signature not in plain:
        footer.append(signature)
    existing = unescape(body + "\n" + "\n".join(footer))
    links = []
    for label, key in PROFILE_LINKS:
        url = str(values.get(key) or "").strip()
        if url and url not in existing:
            links.append(f"{label}: {url}")
            existing += "\n" + url
    if links:
        footer.append("\n".join(links))
    suffix = "\n\n".join(footer)
    plain = "\n\n".join(part for part in (plain, suffix) if part)
    if is_html:
        html = body + ("\n" + render_html("{{ footer }}", {"footer": suffix}) if suffix else "")
    else:
        html = render_html("{{ body }}", {"body": plain})
    return plain, html
