#!/usr/bin/env python3
"""Extract selected English auth labels from immutable HTML JSON, without executing it."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
CAPTURED_AT = "2026-10-28T10:48:45.546100+00:00"
SOURCE = {
    "url": "https://pump.fun/live",
    "final_url": "https://pump.fun/live",
    "status": 200,
    "path": "evidence/web/objects/c45d40b52df03727",
    "bytes": 785309,
    "sha256": "aeff704c15d99482fe6e6347a92db0170dffeceb940a70e61dcc10002b006355",
}
OUTPUT = "packages/frontend/src/app/auth/auth-copy.json"
KEYS = (
    "common.sign_in", "common.close", "common.back", "web.common.try_again",
    "web.auth.refresh_the_page", "web.auth.opening_sign_in", "web.auth.loading_wallet_options",
    "web.auth.sign_in_open_failed_title", "web.auth.sign_in_error_description",
    "web.auth.sign_in_timeout_description", "web.auth.continue_with_github",
    "web.auth.continue_with_social", "web.auth.email_address_label", "web.auth.email_placeholder",
    "web.auth.send_sign_in_code", "web.auth.session_lapsed_signed_out", "web.wallet.welcome_back",
    "web.wallet.sign_in_to_start_trading", "web.wallet.select_wallet", "web.wallet.more_wallets",
    "web.wallet.or_connect_wallet", "web.wallet.recent", "web.wallet.detected",
)


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.current: list[str] | None = None
        self.scripts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.scripts.append("".join(self.current))
            self.current = None


def extract(html: str) -> dict[str, str]:
    parser = Scripts()
    parser.feed(html)
    chunks = []
    for script in parser.scripts:
        if not script.startswith("self.__next_f.push("):
            continue
        match = re.fullmatch(r"self\.__next_f\.push\((.*)\)", script, re.S)
        if not match:
            raise ValueError("Unsupported Flight push syntax")
        item = json.loads(match[1])
        if isinstance(item, list) and len(item) == 2 and item[0] == 1 and isinstance(item[1], str):
            chunks.append(item[1])
    rows = [line[3:] for line in "".join(chunks).split('\n') if line.startswith("c6:")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one captured c6 locale record")
    locale = json.loads(rows[0])
    if not isinstance(locale, dict) or locale.get("locale") != "en":
        raise ValueError("Expected English locale")
    result = {}
    for key in KEYS:
        value = locale.get("resources")
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                raise ValueError(f"Missing captured label: {key}")
            value = value[part]
        if not isinstance(value, str) or not value:
            raise ValueError(f"Invalid captured label: {key}")
        result[key] = value
    return result


def generate(root: Path) -> str:
    manifest = json.loads((root / "evidence/web/manifest.json").read_text())
    if manifest.get("captured_at") != CAPTURED_AT:
        raise ValueError("Capture timestamp differs from the reviewed checkpoint")
    matches = [row for row in manifest["records"] if row.get("url") == SOURCE["url"]]
    if len(matches) != 1 or any(matches[0].get(key) != value for key, value in SOURCE.items()):
        raise ValueError("Captured auth locale manifest identity differs")
    raw = (root / SOURCE["path"]).read_bytes()
    if len(raw) != SOURCE["bytes"] or hashlib.sha256(raw).hexdigest() != SOURCE["sha256"]:
        raise ValueError("Captured auth locale bytes differ")
    return json.dumps(extract(raw.decode("utf-8", errors="strict")), ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=APP_ROOT)
    args = parser.parse_args()
    expected = generate(args.root)
    output = args.root / OUTPUT
    if args.check:
        if output.read_text() != expected:
            raise SystemExit("Auth labels differ from authenticated captured JSON")
        print(f"Verified {len(KEYS)} auth labels from retained /live Flight c6 (no JavaScript execution)")
    else:
        output.write_text(expected)


if __name__ == "__main__":
    main()
