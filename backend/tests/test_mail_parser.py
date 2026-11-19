"""Synthetic MIME fixtures exercising content selection and resource boundaries."""

import hashlib
from dataclasses import replace
from email import policy
from email.message import EmailMessage

import pytest

from app.services.mail_parser import DEFAULT_LIMITS, MessageRejected, parse_message


def raw_message(body="A useful body.", subject="Meeting notes"):
    message = EmailMessage()
    message["Subject"] = subject
    message.set_content(body)
    return message


def test_encoded_subject_body_and_canonical_content_hash():
    raw = (
        b"Subject: =?iso-8859-1?q?Caf=E9?=\r\n"
        b"Content-Type: text/plain; charset=iso-8859-1\r\n\r\n"
        b"  Cr\xe8me\t br\xfbl\xe9e\r\n"
    )
    parsed = parse_message(raw)
    assert parsed.subject_text == "Café"
    assert parsed.body_text == "Crème brûlée"
    assert parsed.model_text == "Café\nCrème brûlée"
    assert parsed.character_count == len(parsed.model_text)
    assert parsed.content_sha256 == hashlib.sha256(parsed.model_text.encode()).hexdigest()


def test_plain_alternative_is_used_once():
    message = raw_message("Plain choice")
    message.add_alternative("<p>HTML duplicate must not enter the model</p>", subtype="html")
    parsed = parse_message(message.as_bytes())
    assert parsed.body_text == "Plain choice"
    assert "html_fallback" not in parsed.parse_warnings


def test_blank_plain_alternative_falls_back_to_html():
    message = raw_message("   ")
    message.add_alternative("<p>Visible HTML</p>", subtype="html")
    parsed = parse_message(message.as_bytes())
    assert parsed.body_text == "Visible HTML"
    assert "html_fallback" in parsed.parse_warnings


def test_html_is_plain_text_without_script_style_attributes_or_fetches(monkeypatch):
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("network access"))
    message = raw_message()
    message.set_content(
        '<head><title>head secret</title></head><script src="https://example.com/">'
        "script secret</script><style>style secret</style><p>Hello &amp; welcome</p>"
        '<img src="https://example.com/tracker"><a href="https://example.com/">Read more</a>'
        '<iframe src="https://example.com/">frame secret</iframe>',
        subtype="html",
    )
    parsed = parse_message(message.as_bytes())
    assert parsed.body_text == "Hello & welcome Read more"
    assert "https://" not in parsed.body_text


def test_mixed_inline_text_is_combined_but_attachments_are_ignored():
    message = raw_message("Main body")
    message.make_mixed()
    inline = EmailMessage()
    inline.set_content("Inline continuation")
    message.attach(inline)
    message.add_attachment("Attachment private marker", filename="notes.txt")
    attached = raw_message("Forwarded private marker", "Forwarded subject")
    message.add_attachment(attached)
    parsed = parse_message(message.as_bytes())
    assert parsed.body_text == "Main body Inline continuation"
    assert "private marker" not in parsed.model_text
    assert "Forwarded subject" not in parsed.model_text


def test_named_inline_text_is_not_used_as_body():
    message = raw_message("Main body")
    message.add_attachment("Named inline marker", filename="inline.txt", disposition="inline")
    assert parse_message(message.as_bytes()).body_text == "Main body"


def test_related_content_id_selects_main_body():
    message = EmailMessage()
    message["Subject"] = "Related"
    message.make_related()
    resource = EmailMessage()
    resource.set_content(b"not an image", maintype="image", subtype="png")
    resource["Content-ID"] = "<resource>"
    message.attach(resource)
    html = EmailMessage()
    html.set_content("<p>Related main body</p>", subtype="html")
    html["Content-ID"] = "<main>"
    message.attach(html)
    message.set_param("start", "<main>")
    assert parse_message(message.as_bytes()).body_text == "Related main body"


def test_unknown_charset_and_invalid_octets_are_reported():
    parsed = parse_message(
        b"Subject: Example\nContent-Type: text/plain; charset=unknown-charset\n\n\x81bad\xff"
    )
    assert parsed.body_text == "�badÿ"
    assert {"charset_fallback", "replacement_characters"}.issubset(parsed.parse_warnings)


def test_unencoded_utf8_subject_and_unicode_normalization():
    parsed = parse_message("Subject: Café\n\nCafe\u0301  body\x00 text".encode())
    assert parsed.subject_text == "Café"
    assert parsed.body_text == "Café body text"


def test_transport_and_classification_headers_are_not_features():
    raw = (
        b"From: sender-private@example.com\nX-Spam-Status: classification-leak\n"
        b"Received: transport-leak\nSubject: Public subject\n\nPublic body"
    )
    assert parse_message(raw).model_text == "Public subject\nPublic body"


def test_subject_only_email_and_duplicate_subject_policy():
    parsed = parse_message(b"Subject: First subject\nSubject: Ignored subject\n\n")
    assert parsed.model_text == "First subject"
    assert "duplicate_subject" in parsed.parse_warnings


@pytest.mark.parametrize(
    "raw,reason",
    [
        (b"\n\n   ", "empty_text"),
        (b"Content-Type: text/html\n\n<script>only code</script>", "empty_text"),
        (b"this is not a MIME header\nmore text", "malformed_mime"),
        (b"Content-Type: multipart/mixed; boundary=missing\n\nbody", "malformed_mime"),
    ],
)
def test_malformed_or_empty_messages_have_fixed_reasons(raw, reason):
    with pytest.raises(MessageRejected, match=reason):
        parse_message(raw)


def test_message_header_and_text_limits():
    with pytest.raises(MessageRejected, match="message_limit"):
        parse_message(b"x" * 17, replace(DEFAULT_LIMITS, message_bytes=16))
    with pytest.raises(MessageRejected, match="header_limit"):
        parse_message(
            b"Subject: " + b"x" * 30 + b"\n\nbody", replace(DEFAULT_LIMITS, header_bytes=16)
        )
    with pytest.raises(MessageRejected, match="text_limit"):
        parse_message(
            raw_message("long body").as_bytes(), replace(DEFAULT_LIMITS, text_characters=5)
        )


def test_mime_part_and_depth_limits():
    message = raw_message()
    message.make_mixed()
    for _ in range(4):
        child = raw_message()
        message.attach(child)
    with pytest.raises(MessageRejected, match="mime_parts_limit"):
        parse_message(message.as_bytes(), replace(DEFAULT_LIMITS, mime_parts=3))
    nested = raw_message()
    for _ in range(4):
        parent = EmailMessage()
        parent.make_mixed()
        parent.attach(nested)
        nested = parent
    with pytest.raises(MessageRejected, match="mime_depth_limit"):
        parse_message(nested.as_bytes(), replace(DEFAULT_LIMITS, mime_depth=2))


def test_nested_headers_have_the_same_limit():
    message = raw_message()
    message.make_mixed()
    child = raw_message()
    child["X-Large"] = "x" * 3000
    message.attach(child)
    with pytest.raises(MessageRejected, match="header_limit"):
        parse_message(
            message.as_bytes(policy=policy.SMTP), replace(DEFAULT_LIMITS, header_bytes=1000)
        )


def test_invalid_limits_are_not_accepted():
    with pytest.raises(ValueError, match="invalid_parse_limits"):
        replace(DEFAULT_LIMITS, mime_parts=0)
