from __future__ import annotations

from dataclasses import dataclass
import html
import re


ENTRY_START_RE = re.compile(r"(?m)^\\\\\s*\narXiv:")
END_RE = re.compile(r"(?ms)^\\\\\s*\(\s*(https://arxiv\.org/abs/[^\s,]+)\s*,\s*([^)]+)\)")
FIELD_RE = re.compile(r"^(Title|Authors|Categories|Comments|Report-no):\s*(.*)$")


@dataclass(frozen=True)
class ArxivPaper:
    arxiv_id: str
    date: str
    size: str
    title: str
    authors: str
    categories: tuple[str, ...]
    abstract: str
    url: str
    comments: str = ""
    report_no: str = ""

    @property
    def text_for_matching(self) -> str:
        return " ".join(
            [
                self.title,
                self.authors,
                " ".join(self.categories),
                self.comments,
                self.abstract,
            ]
        ).lower()


def parse_daily_email(text: str) -> list[ArxivPaper]:
    """Parse an arXiv daily email body into structured paper records."""
    text = _normalize_email_text(text)
    starts = [match.start() for match in ENTRY_START_RE.finditer(text)]
    papers: list[ArxivPaper] = []

    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        block = text[start:end].strip()
        paper = _parse_entry(block)
        if paper is not None:
            papers.append(paper)

    return papers


def _normalize_email_text(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    return text


def _parse_entry(block: str) -> ArxivPaper | None:
    lines = block.splitlines()
    if len(lines) < 2:
        return None

    arxiv_line_index = next((i for i, line in enumerate(lines) if line.startswith("arXiv:")), None)
    if arxiv_line_index is None:
        return None

    arxiv_id = lines[arxiv_line_index].removeprefix("arXiv:").strip()
    date_line = lines[arxiv_line_index + 1].strip() if arxiv_line_index + 1 < len(lines) else ""
    date, size = _parse_date_and_size(date_line)

    end_match = END_RE.search(block)
    url = end_match.group(1).strip() if end_match else f"https://arxiv.org/abs/{arxiv_id}"
    if end_match:
        size = end_match.group(2).strip() or size

    content_lines = lines[arxiv_line_index + 2 :]
    if end_match:
        end_line = block[: end_match.start()].count("\n")
        content_lines = lines[arxiv_line_index + 2 : end_line]

    fields, abstract = _parse_fields_and_abstract(content_lines)

    title = fields.get("Title", "")
    authors = fields.get("Authors", "")
    categories = tuple(fields.get("Categories", "").split())

    if not title or not authors or not categories or not abstract:
        return None

    return ArxivPaper(
        arxiv_id=arxiv_id,
        date=date,
        size=size,
        title=title,
        authors=authors,
        categories=categories,
        comments=fields.get("Comments", ""),
        report_no=fields.get("Report-no", ""),
        abstract=abstract,
        url=url,
    )


def _parse_date_and_size(line: str) -> tuple[str, str]:
    match = re.match(r"Date:\s*(.*?)\s*(?:\(([^)]*)\))?\s*$", line)
    if not match:
        return line, ""
    return match.group(1).strip(), (match.group(2) or "").strip()


def _parse_fields_and_abstract(lines: list[str]) -> tuple[dict[str, str], str]:
    fields: dict[str, list[str]] = {}
    current_field: str | None = None
    abstract_lines: list[str] = []
    in_abstract = False

    for raw_line in lines:
        line = raw_line.rstrip()
        if line == "\\\\":
            in_abstract = True
            current_field = None
            continue

        if not in_abstract:
            match = FIELD_RE.match(line)
            if match:
                current_field = match.group(1)
                fields.setdefault(current_field, []).append(match.group(2).strip())
                continue
            if current_field and (line.startswith("  ") or not line.strip()):
                fields[current_field].append(line.strip())
                continue

        if in_abstract and line.strip():
            abstract_lines.append(line.strip())

    normalized_fields = {
        name: _normalize_wrapped_text(parts)
        for name, parts in fields.items()
    }
    abstract = _normalize_wrapped_text(abstract_lines)
    return normalized_fields, abstract


def _normalize_wrapped_text(parts: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip()
