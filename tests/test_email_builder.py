from utils.email_builder import build_email_message


def test_build_email_contains_plain_html_and_pdf_attachment(tmp_path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"resume bytes")
    message = build_email_message(
        sender="me@example.com",
        recipient="recruiter@example.com",
        subject="Hello {{ recipient_name }}",
        body_template="Hi {{ recipient_name }},\n\nSee https://example.com",
        values={"recipient_name": "Alex"},
        attachment_path=resume,
    )

    assert message["To"] == "recruiter@example.com"
    assert message["Subject"] == "Hello Alex"
    assert "https://example.com" in message.get_body("plain").get_content()
    assert "https://example.com" in message.get_body("html").get_content()
    assert any(part.get_filename() == "resume.pdf" for part in message.iter_attachments())
