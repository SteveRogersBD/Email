"""Build MIME messages suitable for Gmail API delivery."""

from __future__ import annotations

import mimetypes
import re
from email.message import EmailMessage
from html import escape
from pathlib import Path

from services.template_service import render_html, render_text


URL_PATTERN = re.compile(r"(https?://[^\s<]+)")


def linkify_html(text: str) -> str:
    escaped = escape(text)
    return URL_PATTERN.sub(r'<a href="\1">\1</a>', escaped).replace("\n", "<br>\n")


def build_html_body(rendered_text: str) -> str:
    """Convert rendered text to a compact HTML email with clickable URLs."""

    if "<p>" in rendered_text or "<html" in rendered_text.lower():
        return rendered_text
    paragraphs = [part.strip() for part in rendered_text.split("\n\n") if part.strip()]
    return "\n\n".join(f"<p>{linkify_html(paragraph)}</p>" for paragraph in paragraphs)


def build_email_message(
    *,
    sender: str,
    recipient: str,
    subject: str,
    body_template: str,
    values: dict[str, object],
    attachment_path: str | Path | None = None,
) -> EmailMessage:
    """Create a plain-text + HTML MIME message, optionally with a PDF resume."""

    rendered_text = render_text(body_template, values)
    rendered_html = render_html(body_template, values)
    if "<" not in body_template or ">" not in body_template:
        rendered_html = build_html_body(rendered_text)

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(rendered_text)
    message.add_alternative(rendered_html, subtype="html")

    if attachment_path:
        path = Path(attachment_path)
        content_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
        message.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
    return message
