"""SQLite persistence for templates, settings, and outreach history."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import DateTime, Integer, String, Text, create_engine, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    default_links: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    recipient_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    company: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    template_used: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    gmail_message_id: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    send_status: Mapped[str] = mapped_column(String(30), nullable=False)
    error_details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attachment_names: Mapped[str] = mapped_column(Text, default="", nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="", nullable=False)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create database tables if they do not exist."""

    settings.ensure_directories()
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_templates() -> list[EmailTemplate]:
    with session_scope() as session:
        return list(session.scalars(select(EmailTemplate).order_by(EmailTemplate.name)))


def get_template(template_id: int) -> EmailTemplate | None:
    with session_scope() as session:
        return session.get(EmailTemplate, template_id)


def upsert_template(name: str, subject: str, body: str, default_links: str = "", template_id: int | None = None) -> EmailTemplate:
    with session_scope() as session:
        template = session.get(EmailTemplate, template_id) if template_id else None
        if template is None:
            template = EmailTemplate(name=name, subject=subject, body=body, default_links=default_links)
            session.add(template)
        else:
            template.name = name
            template.subject = subject
            template.body = body
            template.default_links = default_links
        session.flush()
        session.refresh(template)
        return template


def delete_template(template_id: int) -> None:
    with session_scope() as session:
        template = session.get(EmailTemplate, template_id)
        if template:
            session.delete(template)


def get_setting(key: str, default: str = "") -> str:
    with session_scope() as session:
        item = session.get(AppSetting, key)
        return item.value if item else default


def set_setting(key: str, value: str) -> None:
    with session_scope() as session:
        item = session.get(AppSetting, key)
        if item is None:
            session.add(AppSetting(key=key, value=value))
        else:
            item.value = value


def record_outreach(**values: str) -> Outreach:
    with session_scope() as session:
        item = Outreach(**values)
        session.add(item)
        session.flush()
        session.refresh(item)
        return item


def was_contacted(recipient_email: str) -> bool:
    with session_scope() as session:
        statement = select(Outreach.id).where(
            Outreach.recipient_email == recipient_email.strip().lower(),
            Outreach.send_status == "sent",
        ).limit(1)
        return session.scalar(statement) is not None


def list_outreach(search: str = "") -> list[Outreach]:
    with session_scope() as session:
        statement = select(Outreach).order_by(Outreach.sent_at.desc())
        if search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(Outreach.recipient_email.ilike(term), Outreach.recipient_name.ilike(term), Outreach.company.ilike(term))
            )
        return list(session.scalars(statement))


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
    with session_scope() as session:
        existing = set(session.scalars(select(EmailTemplate.name)))
        for values in starter_templates():
            if values["name"] not in existing:
                session.add(EmailTemplate(**values))
