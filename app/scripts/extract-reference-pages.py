#!/usr/bin/env python3
"""Extract authenticated reference-page content from retained server HTML."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = APP_ROOT / "evidence/web/manifest.json"
OUTPUT_PATH = (
    APP_ROOT
    / "packages/frontend/src/app/docs/reference-pages.generated.json"
)
CAPTURED_AT = "2026-10-28T10:48:45.546100+00:00"

SOURCES = {
    "fees": {
        "route": "/docs/fees",
        "url": "https://pump.fun/docs/fees",
        "title": "Fees",
        "path": "evidence/web/objects/34f7b585a78296af",
        "bytes": 370_412,
        "sha256": "6e0dd8524a735bf232d28e2153ea3e835565dcbf653964acdac8f93168be2f72",
        "counts": {"h2": 7, "h3": 0, "p": 19, "table": 7, "ul": 0},
    },
    "privacy": {
        "route": "/docs/privacy-policy",
        "url": "https://pump.fun/docs/privacy-policy",
        "title": "Privacy Notice",
        "path": "evidence/web/objects/ecde4a73aafb477e",
        "bytes": 355_497,
        "sha256": "babc5695f31c07f667f321e2c4456ae37e478bc77eac77ca2b724878daf13cc7",
        "counts": {"h2": 16, "h3": 7, "p": 62, "table": 0, "ul": 4},
    },
    "terms": {
        "route": "/docs/terms-and-conditions",
        "url": "https://pump.fun/docs/terms-and-conditions",
        "title": "Terms Of Use",
        "path": "evidence/web/objects/1e06d459af096a65",
        "bytes": 698_394,
        "sha256": "f6ffed345dfb40e8f8fc4fec31b522e10663d19783508849ba75642b16dd4be2",
        "counts": {"h2": 36, "h3": 2, "p": 482, "table": 0, "ul": 4},
    },
}

ALLOWED_TAGS = {
    "main",
    "h1",
    "h2",
    "h3",
    "p",
    "section",
    "div",
    "span",
    "strong",
    "a",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
}


class ExtractionError(RuntimeError):
    pass


@dataclass
class Node:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)


class TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def walk(node: Node):
    yield node
    for child in node.children:
        if isinstance(child, Node):
            yield from walk(child)


def text_content(node: Node) -> str:
    return "".join(
        child if isinstance(child, str) else text_content(child)
        for child in node.children
    )


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    if not result:
        raise ExtractionError(f"Heading cannot produce an anchor: {value!r}")
    return result


def append_text(items: list[Any], value: str) -> None:
    collapsed = re.sub(r"\s+", " ", value)
    if not collapsed:
        return
    if items and isinstance(items[-1], str):
        items[-1] += collapsed
    else:
        items.append(collapsed)


def clean_inline_edges(items: list[Any]) -> list[Any]:
    if items and isinstance(items[0], str):
        items[0] = items[0].lstrip()
    if items and isinstance(items[-1], str):
        items[-1] = items[-1].rstrip()
    return [item for item in items if item != ""]


def inline_children(node: Node, trim: bool = True) -> list[Any]:
    result: list[Any] = []
    for child in node.children:
        if isinstance(child, str):
            append_text(result, child)
            continue
        if child.tag in {"span"}:
            for item in inline_children(child, trim=False):
                if isinstance(item, str):
                    append_text(result, item)
                else:
                    result.append(item)
            continue
        if child.tag == "strong":
            result.append({"type": "strong", "children": inline_children(child, trim=False)})
            continue
        if child.tag == "a":
            href = child.attrs.get("href")
            if not isinstance(href, str) or not (
                href.startswith("/")
                or href.startswith("https://")
                or href.startswith("mailto:")
            ):
                raise ExtractionError(f"Unsupported link target: {href!r}")
            result.append(
                {"type": "link", "href": href, "children": inline_children(child, trim=False)}
            )
            continue
        raise ExtractionError(f"Unexpected inline element <{child.tag}>")
    # Only block-level callers trim; nested inline elements keep the spaces
    # that separate them from neighbouring text (e.g. after a bold label).
    return clean_inline_edges(result) if trim else [item for item in result if item != ""]


def descendants(node: Node, tag: str) -> list[Node]:
    return [candidate for candidate in walk(node) if candidate.tag == tag]


def table_block(node: Node) -> dict[str, Any]:
    def check_children(parent, allowed):
        for child in parent.children:
            if isinstance(child, str):
                if child.strip(): raise ExtractionError('Unrepresented table text')
            elif child.tag not in allowed:
                raise ExtractionError('Unrepresented table element')
            elif child.tag in {'thead', 'tbody'}:
                check_children(child, {'tr'})
            elif child.tag == 'tr':
                check_children(child, {'td', 'th'})
    check_children(node, {'thead', 'tbody', 'tr'})
    rows = []
    for row in descendants(node, "tr"):
        cells = []
        for child in row.children:
            if isinstance(child, Node) and child.tag in {"th", "td"}:
                cells.append(
                    {
                        "header": child.tag == "th",
                        "children": inline_children(child),
                    }
                )
        if not cells:
            raise ExtractionError("Captured table contains an empty row")
        rows.append({"cells": cells})
    if not rows:
        raise ExtractionError("Captured table contains no rows")
    return {"type": "table", "rows": rows}


def list_block(node: Node) -> dict[str, Any]:
    for child in node.children:
        if (isinstance(child, str) and child.strip()) or (isinstance(child, Node) and child.tag != 'li'):
            raise ExtractionError('Unrepresented list content')
    items = [
        {"children": inline_children(child)}
        for child in node.children
        if isinstance(child, Node) and child.tag == "li"
    ]
    if not items:
        raise ExtractionError("Captured list contains no direct items")
    return {"type": "list", "ordered": node.tag == "ol", "items": items}


def blocks(node: Node, seen_ids: set[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for child in node.children:
        if isinstance(child, str):
            if child.strip():
                raise ExtractionError(
                    f"Unexpected free text below <{node.tag}>: {child.strip()[:80]!r}"
                )
            continue
        if child.tag == "h1":
            continue
        if child.tag in {"section", "div", "thead", "tbody"}:
            result.extend(blocks(child, seen_ids))
            continue
        if child.tag in {"h2", "h3"}:
            heading = normalized_text(text_content(child))
            identity = slug(heading)
            if identity in seen_ids:
                raise ExtractionError(f"Duplicate section identity: {identity}")
            seen_ids.add(identity)
            result.append(
                {
                    "type": "heading",
                    "level": int(child.tag[1]),
                    "id": identity,
                    "text": heading,
                }
            )
            continue
        if child.tag == "p":
            content = inline_children(child)
            if not content:
                raise ExtractionError("Captured document contains an empty paragraph")
            result.append({"type": "paragraph", "children": content})
            continue
        if child.tag in {"ul", "ol"}:
            result.append(list_block(child))
            continue
        if child.tag == "table":
            result.append(table_block(child))
            continue
        raise ExtractionError(f"Unexpected block element <{child.tag}>")
    return result


def element_counts(main: Node) -> dict[str, int]:
    return {
        tag: sum(1 for node in walk(main) if node.tag == tag)
        for tag in ("h2", "h3", "p", "table", "ul")
    }


def find_document_main(root: Node, title: str) -> Node:
    matches = []
    for node in walk(root):
        if node.tag != "main":
            continue
        h1s = [
            child
            for child in node.children
            if isinstance(child, Node) and child.tag == "h1"
        ]
        if len(h1s) == 1 and normalized_text(text_content(h1s[0])) == title:
            matches.append(node)
    if len(matches) != 1:
        raise ExtractionError(
            f"Expected one document main for {title!r}, found {len(matches)}"
        )
    return matches[0]


def require_document_markers(key: str, document: dict[str, Any]) -> None:
    rendered = json.dumps(document["blocks"], ensure_ascii=False)
    if "Last Updated: 17 October 2026" not in rendered:
        raise ExtractionError(f"{key}: unsupported or missing Last Updated date")
    if key == "fees":
        required = [
            "Creator fee",
            "Protocol fee",
            "LP fee",
            "Total fee",
            "Holder Rewards coins",
            "Platform Fee",
        ]
        for marker in required:
            if marker not in rendered:
                raise ExtractionError(f"fees: missing required fee data {marker!r}")


def verify_manifest(manifest: Any, source: dict[str, Any]) -> None:
    if not isinstance(manifest, dict) or manifest.get("captured_at") != CAPTURED_AT:
        raise ExtractionError("Capture manifest timestamp does not match")
    records = manifest.get("records")
    if not isinstance(records, list):
        raise ExtractionError("Capture manifest records are missing")
    matches = [record for record in records if record.get("url") == source["url"]]
    if len(matches) != 1:
        raise ExtractionError(f"Expected one manifest record for {source['url']}")
    record = matches[0]
    expected = {
        "final_url": source["url"],
        "status": 200,
        "path": source["path"],
        "bytes": source["bytes"],
        "sha256": source["sha256"],
    }
    if any(record.get(field) != value for field, value in expected.items()):
        raise ExtractionError(f"Manifest provenance mismatch for {source['url']}")
    content_type = record.get("headers", {}).get("content-type")
    if content_type != "text/html; charset=utf-8":
        raise ExtractionError(f"Unexpected content type for {source['url']}")


def parse_document_bytes(
    key: str, source: dict[str, Any], data: bytes
) -> dict[str, Any]:
    if len(data) != source["bytes"]:
        raise ExtractionError(f"{key}: byte count mismatch")
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256 != source["sha256"]:
        raise ExtractionError(f"{key}: SHA-256 mismatch")
    try:
        html = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ExtractionError(f"{key}: captured HTML is not UTF-8") from error

    parser = TreeParser()
    parser.feed(html)
    main = find_document_main(parser.root, source["title"])
    unexpected = sorted({node.tag for node in walk(main)} - ALLOWED_TAGS)
    if unexpected:
        raise ExtractionError(f"{key}: unexpected document tags {unexpected}")
    counts = element_counts(main)
    if counts != source["counts"]:
        raise ExtractionError(
            f"{key}: document structure changed: expected {source['counts']}, got {counts}"
        )

    document = {
        "key": key,
        "route": source["route"],
        "officialUrl": source["url"],
        "title": source["title"],
        "source": {
            "path": source["path"],
            "bytes": source["bytes"],
            "sha256": source["sha256"],
            "capturedAt": CAPTURED_AT,
            "status": 200,
            "contentType": "text/html; charset=utf-8",
        },
        "blocks": blocks(main, set()),
        "observedCounts": counts,
    }
    require_document_markers(key, document)
    canonical_blocks = json.dumps(
        document["blocks"], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    document["contentSha256"] = hashlib.sha256(canonical_blocks).hexdigest()
    return document


def extract_document(
    key: str, source: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    verify_manifest(manifest, source)
    return parse_document_bytes(key, source, (APP_ROOT / source["path"]).read_bytes())


def generate() -> str:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    output = {
        "schemaVersion": 1,
        "capturedAt": CAPTURED_AT,
        "documents": [
            extract_document(key, source, manifest)
            for key, source in SOURCES.items()
        ],
    }
    return json.dumps(output, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        generated = generate()
        if args.write:
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(generated, encoding="utf-8")
        else:
            if not OUTPUT_PATH.is_file():
                raise ExtractionError(f"Generated artifact is missing: {OUTPUT_PATH}")
            if OUTPUT_PATH.read_text(encoding="utf-8") != generated:
                raise ExtractionError("Generated reference-page artifact is stale")
    except (ExtractionError, OSError, json.JSONDecodeError) as error:
        print(f"reference-page extraction failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
