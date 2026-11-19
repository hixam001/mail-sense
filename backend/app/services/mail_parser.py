"""Bounded MIME decoding to canonical plain text; never render or fetch content."""

import hashlib
import unicodedata
from dataclasses import asdict, dataclass
from email import errors, policy
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from html.parser import HTMLParser

PREPROCESSING_VERSION = "mime-v1"
WARNING_CODES = {
    "charset_fallback",
    "replacement_characters",
    "mime_defect",
    "html_fallback",
    "duplicate_subject",
    "subject_decode_fallback",
}


@dataclass(frozen=True)
class ParseLimits:
    message_bytes: int = 2 * 1024 * 1024
    header_bytes: int = 64 * 1024
    mime_parts: int = 128
    mime_depth: int = 20
    text_characters: int = 1_000_000
    archive_expanded_bytes: int = 128 * 1024 * 1024
    archive_members: int = 20_000
    output_bytes: int = 512 * 1024 * 1024

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in asdict(self).values()):
            raise ValueError("invalid_parse_limits")


DEFAULT_LIMITS = ParseLimits()


class MessageRejected(ValueError):
    """A fixed reason code suitable for reports without private message text."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ParsedText:
    subject_text: str
    body_text: str
    model_text: str
    character_count: int
    content_sha256: str
    parse_warnings: tuple[str, ...]


def normalize_text(text):
    text = unicodedata.normalize("NFC", text)
    text = "".join(" " if unicodedata.category(c) in {"Cc", "Cs"} else c for c in text)
    return " ".join(text.split())


def _decode(data, charset, warnings):
    try:
        text = data.decode(charset or "utf-8", errors="strict")
    except (LookupError, UnicodeError):
        warnings.add("charset_fallback")
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeError:
            text = data.decode("cp1252", errors="replace")
    if "\ufffd" in text:
        warnings.add("replacement_characters")
    return text


class _HTMLText(HTMLParser):
    blocked_tags = {"script", "style", "head", "template", "iframe", "object", "svg", "math"}
    breaks = {"br", "p", "div", "li", "tr", "td", "h1", "h2", "h3", "hr", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocked = []
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in self.blocked_tags:
            self.blocked.append(tag)
        elif not self.blocked and tag in self.breaks:
            self.chunks.append(" ")

    def handle_startendtag(self, tag, attrs):
        if not self.blocked and tag in self.breaks:
            self.chunks.append(" ")

    def handle_endtag(self, tag):
        if tag in self.blocked:
            while self.blocked.pop() != tag:
                pass
        elif not self.blocked and tag in self.breaks:
            self.chunks.append(" ")

    def handle_data(self, data):
        if not self.blocked:
            self.chunks.append(data)


def _body(part, warnings, limits):
    if part.get_content_disposition() == "attachment" or part.get_filename() is not None:
        return "", False
    kind = part.get_content_type()
    if kind.startswith("message/"):
        return "", False
    if part.is_multipart():
        children = list(part.iter_parts())
        if kind == "multipart/related":
            start = part.get_param("start")
            if start:
                chosen = next((p for p in children if p.get("Content-ID") == start), None)
                children = [chosen] if chosen is not None else children[:1]
            else:
                children = children[:1]
        bodies = [_body(child, warnings, limits) for child in children]
        if kind == "multipart/alternative":
            return next(
                ((text, html) for text, html in bodies if text.strip() and not html),
                next(((text, html) for text, html in bodies if text.strip()), ("", False)),
            )
        return "\n".join(text for text, _ in bodies if text), any(html for _, html in bodies)
    if kind not in {"text/plain", "text/html"}:
        return "", False
    data = part.get_payload(decode=True)
    if not isinstance(data, bytes):
        return "", False
    text = _decode(data, part.get_content_charset(), warnings)
    if len(text) > limits.text_characters:
        raise MessageRejected("text_limit")
    if kind == "text/html":
        parser = _HTMLText()
        parser.feed(text)
        parser.close()
        return "".join(parser.chunks), True
    return text, False


def parse_message(raw, limits=DEFAULT_LIMITS):
    if len(raw) > limits.message_bytes:
        raise MessageRejected("message_limit")
    separators = [p for marker in (b"\r\n\r\n", b"\n\n") if (p := raw.find(marker)) >= 0]
    if min(separators, default=len(raw)) > limits.header_bytes:
        raise MessageRejected("header_limit")
    warnings = set()
    created = 0

    def factory(*args, **kwargs):
        nonlocal created
        created += 1
        if created > limits.mime_parts:
            raise MessageRejected("mime_parts_limit")
        return EmailMessage(*args, **kwargs)

    try:
        message = BytesParser(_class=factory, policy=policy.default).parsebytes(raw)
        parts, pending = [], [(message, 0)]
        while pending:
            part, depth = pending.pop()
            if depth > limits.mime_depth:
                raise MessageRejected("mime_depth_limit")
            parts.append(part)
            if (
                sum(len(name) + len(value) + 2 for name, value in part.raw_items())
                > limits.header_bytes
            ):
                raise MessageRejected("header_limit")
            if part.is_multipart():
                pending.extend((p, depth + 1) for p in part.iter_parts())
        severe = (
            errors.StartBoundaryNotFoundDefect,
            errors.CloseBoundaryNotFoundDefect,
            errors.MultipartInvariantViolationDefect,
            errors.NoBoundaryInMultipartDefect,
            errors.MissingHeaderBodySeparatorDefect,
        )
        if any(isinstance(d, severe) for p in parts for d in p.defects):
            raise MessageRejected("malformed_mime")
        subjects = [value for name, value in message.raw_items() if name.lower() == "subject"]
        if len(subjects) > 1:
            warnings.add("duplicate_subject")
        original = subjects[0] if subjects else ""
        try:
            fragments = decode_header(original)
        except errors.HeaderParseError:
            fragments = [(original, None)]
            warnings.add("subject_decode_fallback")
        subject = "".join(
            _decode(
                value if isinstance(value, bytes) else value.encode("utf-8", "surrogateescape"),
                charset,
                warnings,
            )
            for value, charset in fragments
        )
        body, html = _body(message, warnings, limits)
        if html:
            warnings.add("html_fallback")
        if any(p.defects for p in parts):
            warnings.add("mime_defect")
    except MessageRejected:
        raise
    except (RecursionError, ValueError, TypeError, IndexError, errors.MessageError) as error:
        raise MessageRejected("malformed_mime") from error
    subject, body = normalize_text(subject), normalize_text(body)
    model = "\n".join(text for text in (subject, body) if text)
    if not model:
        raise MessageRejected("empty_text")
    if len(model) > limits.text_characters:
        raise MessageRejected("text_limit")
    return ParsedText(
        subject,
        body,
        model,
        len(model),
        hashlib.sha256(model.encode("utf-8")).hexdigest(),
        tuple(sorted(warnings)),
    )
