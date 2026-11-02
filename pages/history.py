"""Outreach history and export UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.outreach_service import list_outreach


def render_history_page() -> None:
    st.header("Outreach history")
    search = st.text_input("Search recipient, name, or company", placeholder="e.g. acme.com")
    records = list_outreach(search)
    sent_count = sum(record.send_status == "sent" for record in records)
    failed_count = sum(record.send_status in {"failed", "unknown"} for record in records)

    first, second, third = st.columns(3)
    first.metric("Matching messages", len(records))
    second.metric("Confirmed sent", sent_count)
    third.metric("Failed or unknown", failed_count)

    rows = [
        {
            "Recipient": record.recipient_email,
            "Name": record.recipient_name,
            "Company": record.company,
            "Job title": record.job_title,
            "Subject": record.subject,
            "Template": record.template_used,
            "Sent (UTC)": record.sent_at.isoformat() if record.sent_at else "",
            "Status": record.send_status,
            "Gmail ID": record.gmail_message_id,
            "Error": record.error_details,
            "Attachments": record.attachment_names,
        }
        for record in records
    ]
    frame = pd.DataFrame(rows)
    st.dataframe(frame, width="stretch", hide_index=True)
    st.download_button(
        "Export CSV",
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name="outreach-history.csv",
        mime="text/csv",
        disabled=frame.empty,
    )
