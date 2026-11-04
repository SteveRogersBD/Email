from services.email_content import render_email_content
from utils.email_builder import build_email_message


PROFILE = {
    "signature": "Best,\nAlex",
    "linkedin_url": "https://linkedin.com/in/alex",
    "github_url": "https://github.com/alex",
    "portfolio_url": "",
}


def test_footer_is_automatic_and_does_not_duplicate_explicit_values():
    for template in ("Hello!", "Hello!\n\n{{ signature }}\n{{ linkedin_url }}"):
        plain, html = render_email_content(template, PROFILE)
        assert plain.count(PROFILE["signature"]) == 1
        assert plain.count(PROFILE["linkedin_url"]) == 1
        assert plain.count(PROFILE["github_url"]) == 1
        assert f'href="{PROFILE["github_url"]}"' in html
        assert "Portfolio:" not in plain


def test_html_template_preserves_existing_links_and_gets_readable_footer():
    plain, html = render_email_content(
        '<p>Hello!</p><a href="{{ linkedin_url }}">Connect with me</a>', PROFILE
    )
    assert "<p>" not in plain
    assert PROFILE["linkedin_url"] in plain
    assert html.count(f'href="{PROFILE["linkedin_url"]}"') == 1
    assert PROFILE["signature"] in plain


def test_sent_email_matches_preview_including_footer():
    expected_plain, expected_html = render_email_content("Hello!", PROFILE)
    message = build_email_message(
        sender="me@example.com", recipient="recruiter@example.com",
        subject="Hello", body_template="Hello!", values=PROFILE,
    )
    assert message.get_body("plain").get_content().strip() == expected_plain
    assert message.get_body("html").get_content().strip() == expected_html
