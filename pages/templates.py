"""Template management UI."""

from __future__ import annotations

import streamlit as st

from services.outreach_service import delete_template, get_setting, list_templates, upsert_template
from services.template_service import validate_template_syntax


def render_templates_page() -> None:
    st.header("Email templates")
    st.caption("Create reusable messages with Jinja variables such as {{ recipient_name }} and {{ company }}.")
    st.info("Your saved signature and profile links are added to every email automatically. Manage them in Settings → Profile and links.")
    saved_links = [
        label for label, key in (
            ("LinkedIn", "linkedin_url"),
            ("GitHub", "github_url"),
            ("Portfolio", "portfolio_url"),
        ) if get_setting(key).strip()
    ]
    st.caption(
        "Links added automatically: " + ", ".join(saved_links)
        if saved_links else "No profile links saved yet. Add them once in Settings."
    )

    templates = list_templates()
    choices = {template.id: template.name for template in templates}
    mode = st.radio("Template action", ["Edit existing", "Create new"], horizontal=True)

    selected_id: int | None = None
    if mode == "Edit existing" and choices:
        selected_id = st.selectbox("Template", list(choices), format_func=lambda value: choices[value])
        selected = next(template for template in templates if template.id == selected_id)
        initial = (selected.name, selected.subject, selected.body, selected.default_links)
    elif mode == "Edit existing":
        st.info("No templates yet. Create your first one below.")
        initial = ("", "", "", "")
    else:
        initial = ("", "", "", "")

    with st.form("template_editor"):
        name = st.text_input("Template name", value=initial[0])
        subject = st.text_input("Subject", value=initial[1])
        body = st.text_area("Body", value=initial[2], height=260)
        submitted = st.form_submit_button("Save template", type="primary")

    if submitted:
        if not name.strip() or not subject.strip() or not body.strip():
            st.error("Name, subject, and body are required.")
        elif syntax_error := validate_template_syntax(body):
            st.error(f"Template syntax error: {syntax_error}")
        else:
            try:
                upsert_template(name.strip(), subject.strip(), body, initial[3], selected_id)
                st.success("Template saved.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save template: {exc}")

    if selected_id and st.button("Delete selected template", type="secondary"):
        delete_template(selected_id)
        st.success("Template deleted.")
        st.rerun()
