from services.template_service import render_html, render_text, validate_template_syntax


def test_missing_optional_variables_render_without_crashing() -> None:
    rendered = render_text("Hi {{ recipient_name or 'there' }} at {{ company or 'your company' }}", {})
    assert rendered == "Hi there at your company"


def test_plain_text_becomes_html_with_paragraphs() -> None:
    rendered = render_html("Hello\n\nThis is a message.", {})
    assert "<p>Hello</p>" in rendered
    assert "<p>This is a message.</p>" in rendered


def test_template_syntax_is_validated() -> None:
    assert validate_template_syntax("Hi {{ name }}") is None
    assert validate_template_syntax("Hi {{ name ")
