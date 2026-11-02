from utils.validators import validate_attachment, validate_email


def test_validate_email_accepts_basic_address() -> None:
    assert validate_email("person@example.com")
    assert not validate_email("not-an-email")


def test_validate_attachment_checks_pdf_and_size(tmp_path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"pdf")
    assert validate_attachment(resume, max_size_mb=1) is None

    text_file = tmp_path / "resume.txt"
    text_file.write_text("not a pdf")
    assert "PDF" in validate_attachment(text_file, max_size_mb=1)
    assert validate_attachment(tmp_path / "missing.pdf", max_size_mb=1) is not None
