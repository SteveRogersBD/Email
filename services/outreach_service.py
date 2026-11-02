"""Lightweight text-file persistence for templates, settings, and send records."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from config import settings


@dataclass
class EmailTemplate:
    id: int
    name: str
    subject: str
    body: str
    default_links: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Outreach:
    id: int
    recipient_email: str
    recipient_name: str
    company: str
    job_title: str
    subject: str
    template_used: str
    sent_at: datetime
    gmail_message_id: str
    send_status: str
    error_details: str
    attachment_names: str


def _read_json(path, default: Any) -> Any:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_templates() -> list[EmailTemplate]:
    return [EmailTemplate(**item) for item in _read_json(settings.templates_file, [])]


def _write_templates(templates: list[EmailTemplate]) -> None:
    _write_json(settings.templates_file, [asdict(template) for template in templates])


def _read_settings() -> dict[str, str]:
    value = _read_json(settings.settings_file, {})
    return value if isinstance(value, dict) else {}


def _read_history() -> list[Outreach]:
    if not settings.history_file.exists():
        return []
    records: list[Outreach] = []
    for line in settings.history_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            item["sent_at"] = datetime.fromisoformat(item["sent_at"])
            records.append(Outreach(**item))
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
    return records


def _append_history(record: Outreach) -> None:
    with settings.history_file.open("a", encoding="utf-8") as file:
        payload = asdict(record)
        payload["sent_at"] = record.sent_at.isoformat()
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def init_db() -> None:
    """Initialize empty local text stores; retained as a compatibility name."""

    settings.ensure_directories()
    if not settings.templates_file.exists():
        _write_json(settings.templates_file, [])
    if not settings.settings_file.exists():
        _write_json(settings.settings_file, {})
    settings.history_file.touch(exist_ok=True)


def list_templates() -> list[EmailTemplate]:
    return sorted(_read_templates(), key=lambda template: template.name.lower())


def get_template(template_id: int) -> EmailTemplate | None:
    return next((template for template in _read_templates() if template.id == template_id), None)


def upsert_template(
    name: str,
    subject: str,
    body: str,
    default_links: str = "",
    template_id: int | None = None,
) -> EmailTemplate:
    templates = _read_templates()
    if any(template.name == name and template.id != template_id for template in templates):
        raise ValueError(f"A template named {name!r} already exists.")
    now = datetime.now(timezone.utc).isoformat()
    template = get_template(template_id) if template_id else None
    if template is None:
        next_id = max((item.id for item in templates), default=0) + 1
        template = EmailTemplate(next_id, name, subject, body, default_links, now, now)
        templates.append(template)
    else:
        template.name = name
        template.subject = subject
        template.body = body
        template.default_links = default_links
        template.updated_at = now
        templates = [item for item in templates if item.id != template.id]
        templates.append(template)
    _write_templates(templates)
    return template


def delete_template(template_id: int) -> None:
    _write_templates([template for template in _read_templates() if template.id != template_id])


def get_setting(key: str, default: str = "") -> str:
    return str(_read_settings().get(key, default))


def set_setting(key: str, value: str) -> None:
    values = _read_settings()
    values[key] = value
    _write_json(settings.settings_file, values)


def record_outreach(**values: str) -> Outreach:
    records = _read_history()
    record = Outreach(
        id=max((item.id for item in records), default=0) + 1,
        sent_at=datetime.now(timezone.utc),
        **values,
    )
    _append_history(record)
    return record


def was_contacted(recipient_email: str) -> bool:
    normalized = recipient_email.strip().lower()
    return any(record.recipient_email == normalized and record.send_status == "sent" for record in _read_history())


def list_outreach(search: str = "") -> list[Outreach]:
    records = _read_history()
    if search.strip():
        term = search.strip().lower()
        records = [
            record
            for record in records
            if term in record.recipient_email.lower()
            or term in record.recipient_name.lower()
            or term in record.company.lower()
        ]
    return sorted(records, key=lambda record: record.sent_at, reverse=True)


def starter_templates() -> list[dict[str, str]]:
    return [
        {
            "name": "General recruiter outreach",
            "subject": "Exploring {{ job_title or 'opportunities' }} at {{ company or 'your company' }}",
            "body": "Hi {{ recipient_name or 'there' }},\n\nI’m reaching out because I’m exploring {{ job_title or 'new opportunities' }} and would love to learn more about {{ company or 'your team' }}.\n\n{{ signature }}",
            "default_links": "linkedin_url,github_url,portfolio_url",
        },
        {
            "name": "Startup founder outreach",
            "subject": "Interested in {{ company or 'your startup' }}",
            "body": "Hi {{ recipient_name or 'there' }},\n\nI’ve been following {{ company or 'your work' }} and was impressed by the problem you’re solving. My background could be a strong fit for a growing team, and I’d welcome a brief conversation.\n\n{{ signature }}",
            "default_links": "linkedin_url,portfolio_url",
        },
        {
            "name": "Follow-up email",
            "subject": "Following up — {{ job_title or 'opportunities' }}",
            "body": "Hi {{ recipient_name or 'there' }},\n\nI wanted to follow up on my note about {{ job_title or 'potential opportunities' }} at {{ company or 'your company' }}. I’d be glad to share more context if useful.\n\n{{ signature }}",
            "default_links": "linkedin_url,github_url,portfolio_url",
        },
    ]


def seed_starter_templates() -> None:
    init_db()
    existing = {template.name for template in _read_templates()}
    for values in starter_templates():
        if values["name"] not in existing:
            upsert_template(**values)
