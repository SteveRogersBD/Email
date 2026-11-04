"""Gmail, profile, and default resume settings UI."""

from __future__ import annotations

import streamlit as st

from config import settings
from services.gmail_service import GmailService
from services.outreach_service import get_setting, set_setting
from utils.validators import validate_attachment


SETTING_KEYS = {
    "full_name": "full_name",
    "signature": "email_signature",
    "linkedin_url": "linkedin_url",
    "github_url": "github_url",
    "portfolio_url": "portfolio_url",
    "default_resume_path": "default_resume_path",
}


def render_settings_page() -> None:
    st.header("Settings")
    st.subheader("Gmail connection")
    gmail = GmailService()
    try:
        connected = gmail.is_connected()
    except Exception:
        connected = False
        st.error("Saved Gmail authorization could not be refreshed. Connect Gmail again to renew access.")
    if connected:
        connected_email = gmail.connected_email()
        st.success(f"Connected as {connected_email}" if connected_email else "Gmail connected. Emails will be sent from the Google account you authorized.")
        if st.button("Disconnect Gmail"):
            gmail.disconnect()
            st.success("Gmail disconnected. Your local token was removed.")
            st.rerun()
    else:
        st.info("Connect Gmail to send. OAuth opens in your browser and never asks this app for your Gmail password.")
        if st.button("Connect Gmail", type="primary"):
            try:
                with st.spinner("Complete Google sign-in in the browser window that opened. Waiting up to 2 minutes…"):
                    gmail.authenticate()
                st.success("Gmail connected.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gmail connection failed: {exc}")

    st.divider()
    st.subheader("Profile and links")
    st.caption("Save these once. Your signature and filled-in links are added to every email automatically and shown in the live preview.")
    with st.form("profile_settings"):
        full_name = st.text_input("Full name", value=get_setting(SETTING_KEYS["full_name"]))
        signature = st.text_area(
            "Email signature",
            value=get_setting(SETTING_KEYS["signature"]),
            height=120,
            help="Automatically added to every email. Existing {{ signature }} placeholders still work without adding it twice.",
        )
        linkedin_url = st.text_input("LinkedIn URL", value=get_setting(SETTING_KEYS["linkedin_url"]))
        github_url = st.text_input("GitHub URL", value=get_setting(SETTING_KEYS["github_url"]))
        portfolio_url = st.text_input("Portfolio URL", value=get_setting(SETTING_KEYS["portfolio_url"]))
        saved = st.form_submit_button("Save profile settings")
    if saved:
        for key, value in {
            "full_name": full_name,
            "email_signature": signature,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
        }.items():
            set_setting(key, value.strip())
        st.success("Profile settings saved.")

    st.divider()
    st.subheader("Default resume")
    current_resume = get_setting(SETTING_KEYS["default_resume_path"])
    if current_resume:
        st.caption(f"Current default: {current_resume}")
    resume = st.file_uploader("Upload or replace default PDF resume", type=["pdf"], key="default_resume_uploader")
    if resume is not None:
        destination = settings.upload_dir / "default_resume.pdf"
        destination.write_bytes(resume.getvalue())
        error = validate_attachment(destination, settings.max_attachment_size_mb)
        if error:
            destination.unlink(missing_ok=True)
            st.error(error)
        else:
            set_setting(SETTING_KEYS["default_resume_path"], str(destination))
            st.success("Default resume saved.")
