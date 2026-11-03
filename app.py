"""Recruiter Outreach Tool Streamlit application."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from config import settings
from pages.settings import render_settings_page
from pages.templates import render_templates_page
from services.gmail_service import GmailService
from services.outreach_service import (
    get_setting,
    init_db,
    list_templates,
    record_outreach,
    seed_starter_templates,
    was_contacted,
)
from services.template_service import render_html, render_text
from utils.email_builder import build_email_message
from utils.validators import validate_attachment, validate_email


def _initialize_app() -> None:
    init_db()
    seed_starter_templates()
    defaults: dict[str, object] = {
        "recipient_email": "",
        "recipient_name": "",
        "company": "",
        "job_title": "",
        "subject": "",
        "body": "",
        "template_id": None,
        "attachment_mode": "Default resume",
        "send_in_progress": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _profile_values() -> dict[str, str]:
    full_name = get_setting("full_name")
    signature = get_setting("email_signature")
    if not signature:
        signature = f"Best,\n{full_name}" if full_name else "Best,"
    links = [
        ("LinkedIn", get_setting("linkedin_url")),
        ("GitHub", get_setting("github_url")),
        ("Portfolio", get_setting("portfolio_url")),
    ]
    link_lines = "\n".join(f"{label}: {url}" for label, url in links if url)
    if link_lines and link_lines not in signature:
        signature = f"{signature.rstrip()}\n{link_lines}"
    return {
        "full_name": full_name,
        "signature": signature,
        "linkedin_url": get_setting("linkedin_url"),
        "github_url": get_setting("github_url"),
        "portfolio_url": get_setting("portfolio_url"),
    }


def _template_values() -> dict[str, str]:
    return {
        "recipient_email": st.session_state.recipient_email,
        "recipient_name": st.session_state.recipient_name,
        "company": st.session_state.company,
        "job_title": st.session_state.job_title,
        **_profile_values(),
    }


def _save_uploaded_resume(uploaded_file) -> Path | None:
    if uploaded_file is None:
        return None
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(uploaded_file.name).name)
    destination = settings.upload_dir / f"compose_{safe_name}"
    destination.write_bytes(uploaded_file.getvalue())
    return destination


def render_compose_page() -> None:
    st.header("Compose outreach")
    st.caption("Personalize a recruiter email, review it, and send exactly one message through Gmail.")
    if message := st.session_state.pop("flash_success", None):
        st.success(message)

    templates = list_templates()
    template_options = {template.id: template for template in templates}
    if not template_options:
        st.warning("No templates are available. Open Templates to create one.")
        return

    current_id = st.session_state.template_id
    if current_id not in template_options:
        current_id = next(iter(template_options))
        st.session_state.template_id = current_id
    selected_id = st.selectbox(
        "Template",
        options=list(template_options),
        index=list(template_options).index(current_id),
        format_func=lambda value: template_options[value].name,
    )
    if selected_id != st.session_state.template_id:
        st.session_state.template_id = selected_id
        selected = template_options[selected_id]
        st.session_state.subject = selected.subject
        st.session_state.body = selected.body
    elif not st.session_state.subject and not st.session_state.body:
        st.session_state.subject = template_options[selected_id].subject
        st.session_state.body = template_options[selected_id].body

    st.subheader("Recipient")
    first, second = st.columns(2)
    with first:
        st.text_input("Recruiter email *", key="recipient_email", placeholder="recruiter@example.com")
        st.text_input("Recruiter name", key="recipient_name")
    with second:
        st.text_input("Company", key="company")
        st.text_input("Job title", key="job_title")

    st.subheader("Email content")
    st.text_input("Subject *", key="subject")
    st.text_area("Body *", key="body", height=280, help="Jinja variables are supported. Missing optional values are safe.")

    st.subheader("Resume attachment")
    attachment_mode = st.radio(
        "Attachment choice",
        ["Default resume", "Choose a different PDF", "No attachment"],
        key="attachment_mode",
        horizontal=True,
    )
    attachment_path: Path | None = None
    if attachment_mode == "Default resume":
        configured = get_setting("default_resume_path")
        attachment_path = Path(configured) if configured else None
        if not configured:
            st.info("No default resume is configured yet. You can set one in Settings.")
    elif attachment_mode == "Choose a different PDF":
        uploaded_file = st.file_uploader("Upload a PDF for this email", type=["pdf"], key="compose_resume_uploader")
        attachment_path = _save_uploaded_resume(uploaded_file)

    values = _template_values()
    rendered_subject = render_text(st.session_state.subject, values)
    rendered_body = render_text(st.session_state.body, values)
    rendered_html = render_html(st.session_state.body, values)
    st.subheader("Preview")
    st.write(f"**To:** {st.session_state.recipient_email or '—'}")
    st.write(f"**Subject:** {rendered_subject or '—'}")
    if rendered_html:
        st.markdown(rendered_html, unsafe_allow_html=True)
    else:
        st.info("Enter a body to preview it.")
    if attachment_path:
        st.caption(f"Attachment: {attachment_path.name}")
    else:
        st.caption("Attachment: none")

    if st.session_state.recipient_email and was_contacted(st.session_state.recipient_email):
        st.warning("This recipient has a previously confirmed sent message in your history.")

    if st.button("Send email", type="primary", disabled=st.session_state.send_in_progress):
        st.session_state.send_in_progress = True
        try:
            errors: list[str] = []
            if not validate_email(st.session_state.recipient_email):
                errors.append("Enter a valid recipient email address.")
            if not rendered_subject:
                errors.append("Subject is required.")
            if not rendered_body:
                errors.append("Body is required.")
            attachment_error = validate_attachment(attachment_path, settings.max_attachment_size_mb)
            if attachment_error:
                errors.append(attachment_error)
            if errors:
                for error in errors:
                    st.error(error)
                return

            gmail = GmailService()
            sender = gmail.connected_email()
            if not sender:
                st.error("Connect Gmail in Settings before sending.")
                return
            message = build_email_message(
                sender=sender,
                recipient=st.session_state.recipient_email.strip(),
                subject=rendered_subject,
                body_template=st.session_state.body,
                values=values,
                attachment_path=attachment_path,
            )
            gmail_message_id = gmail.send_message(message)
            record_outreach(
                recipient_email=st.session_state.recipient_email.strip().lower(),
                recipient_name=st.session_state.recipient_name.strip(),
                company=st.session_state.company.strip(),
                job_title=st.session_state.job_title.strip(),
                subject=rendered_subject,
                template_used=template_options[selected_id].name,
                gmail_message_id=gmail_message_id,
                send_status="sent",
                error_details="",
                attachment_names=attachment_path.name if attachment_path else "",
            )
            st.session_state.recipient_email = ""
            st.session_state.recipient_name = ""
            st.session_state.company = ""
            st.session_state.job_title = ""
            st.session_state.flash_success = f"Email sent successfully. Gmail message ID: {gmail_message_id}"
            st.rerun()
        except TimeoutError as exc:
            record_outreach(
                recipient_email=st.session_state.recipient_email.strip().lower(),
                recipient_name=st.session_state.recipient_name.strip(),
                company=st.session_state.company.strip(),
                job_title=st.session_state.job_title.strip(),
                subject=rendered_subject,
                template_used=template_options[selected_id].name,
                send_status="unknown",
                gmail_message_id="",
                error_details=f"Gmail outcome is unknown because the request timed out: {exc}",
                attachment_names=attachment_path.name if attachment_path else "",
            )
            st.error("The request timed out after contacting Gmail. The outcome is unknown; no automatic retry was made.")
        except Exception as exc:
            record_outreach(
                recipient_email=st.session_state.recipient_email.strip().lower(),
                recipient_name=st.session_state.recipient_name.strip(),
                company=st.session_state.company.strip(),
                job_title=st.session_state.job_title.strip(),
                subject=rendered_subject,
                template_used=template_options[selected_id].name,
                send_status="failed",
                gmail_message_id="",
                error_details=str(exc),
                attachment_names=attachment_path.name if attachment_path else "",
            )
            st.error(f"Email was not sent: {exc}")
        finally:
            st.session_state.send_in_progress = False


def main() -> None:
    st.set_page_config(page_title="Recruiter Outreach", page_icon="✉️", layout="wide")
    _initialize_app()
    st.title("Recruiter Outreach")
    page = st.navigation(
        [
            st.Page(render_compose_page, title="Compose", default=True),
            st.Page(render_templates_page, title="Templates", url_path="templates"),
            st.Page(render_settings_page, title="Settings", url_path="settings"),
        ]
    )
    page.run()


if __name__ == "__main__":
    main()
