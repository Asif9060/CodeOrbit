"""Lesson content rendering helpers."""
from __future__ import annotations

from typing import Iterable
import html
import re
from urllib.parse import urlparse

from django.utils.html import escape
from django.utils.safestring import mark_safe


def render_lesson_content(content: str) -> str:
    if not content:
        return ""

    lines = content.splitlines()
    segments: list[tuple[str, list[str]]] = []
    current: list[str] = []
    current_kind = "text"

    def flush_segment():
        nonlocal current
        if current:
            segments.append((current_kind, current))
            current = []

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("### question"):
            flush_segment()
            current_kind = "question"
            current = []
            continue
        if stripped.lower().startswith("### answer"):
            flush_segment()
            current_kind = "answer"
            current = []
            continue
        if stripped.startswith("### ") and current_kind in ("question", "answer"):
            flush_segment()
            current_kind = "text"
        current.append(line)

    if current:
        segments.append((current_kind, current))

    rendered_parts: list[str] = []
    for kind, seg_lines in segments:
        html = _render_simple_markdown(seg_lines)
        if not html:
            continue
        if kind == "question":
            rendered_parts.append(_wrap_callout("Question", html, "lesson-question"))
        elif kind == "answer":
            rendered_parts.append(_wrap_callout("Answer", html, "lesson-answer"))
        else:
            rendered_parts.append(html)

    return mark_safe("\n".join(rendered_parts))


def _wrap_callout(title: str, body_html: str, css_class: str) -> str:
    return (
        f"<div class=\"lesson-callout {css_class}\">"
        f"<div class=\"lesson-callout-title\">{escape(title)}</div>"
        f"<div class=\"lesson-callout-body\">{body_html}</div>"
        "</div>"
    )


_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _is_safe_url(url: str) -> bool:
    if not url:
        return False
    if url.startswith(("/", "#")):
        return True
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return True
    if parsed.scheme == "mailto" and parsed.path:
        return True
    return False


def _render_inline_markdown(text: str) -> str:
    if not text:
        return ""

    parts = []
    segments = text.split("`")
    for idx, segment in enumerate(segments):
        if idx % 2 == 1:
            parts.append(f"<code>{escape(segment)}</code>")
            continue

        escaped = escape(segment)
        escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
        escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
        escaped = _LINK_RE.sub(_replace_link, escaped)
        parts.append(escaped)

    return "".join(parts)


def _replace_link(match: re.Match) -> str:
    text = match.group(1)
    url = match.group(2)
    raw_url = html.unescape(url).strip()
    if not _is_safe_url(raw_url):
        return match.group(0)
    safe_url = escape(raw_url)
    return f"<a href=\"{safe_url}\" target=\"_blank\" rel=\"noopener\">{text}</a>"


def _render_simple_markdown(lines: Iterable[str]) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            text = " ".join(piece.strip() for piece in paragraph if piece.strip())
            if text:
                blocks.append(f"<p>{_render_inline_markdown(text)}</p>")
            paragraph = []

    def flush_list():
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in list_items)
            blocks.append(f"<ul class=\"lesson-list\">{items}</ul>")
            list_items = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            code = "\n".join(code_lines)
            blocks.append(f"<pre class=\"lesson-code\"><code>{escape(code)}</code></pre>")
            code_lines = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2 class=\"lesson-heading-lg\">{_render_inline_markdown(stripped[3:])}</h2>")
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3 class=\"lesson-heading\">{_render_inline_markdown(stripped[4:])}</h3>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            list_items.append(stripped[2:])
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code:
        flush_code()

    return "\n".join(blocks)
