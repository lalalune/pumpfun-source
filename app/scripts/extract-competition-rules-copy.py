#!/usr/bin/env python3
"""Read authenticated HTML Flight JSON as data; never evaluate captured JavaScript."""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

SOURCE = "evidence/web/objects/d8e580782f84e190"
SHA256 = "1108d23f5f07255ac5e380359b4acc96aabd3b36fb4b6409d1d686bc468050d6"
OUTPUT = "packages/frontend/src/app/leaderboard/competition-rules-copy.json"
RULE_KEYS = (
    "competition_window", "entry", "entry_cap_one", "entry_cap_other",
    "entry_solo", "entry_squad", "list", "open", "range", "registration",
    "rule_join_solo", "rule_join_solo_undated", "rule_join_squad",
    "rule_join_squad_undated", "rule_manipulation", "rule_profit_tracked",
    "rule_squad_pro_rata", "rule_squad_size", "rule_winners",
    "rule_winners_undated", "schedule", "scoring", "scoring_default",
    "terms_link", "title",
)
CUP_KEYS = ("prize_breakdown", "paid_ranks_one", "paid_ranks_other", "tier_range", "tier_single", "tier_each")


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.current = None
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = [] if not any(name == "src" for name, _ in attrs) else None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.scripts.append("".join(self.current))
            self.current = None


def extract(html):
    parser = Scripts()
    parser.feed(html)
    chunks = []
    for script in parser.scripts:
        if not script.startswith("self.__next_f.push("):
            continue
        match = re.fullmatch(r"self\.__next_f\.push\((.*)\)", script, re.S)
        if not match:
            raise ValueError("Unsupported Flight syntax")
        row = json.loads(match[1])
        if isinstance(row, list) and len(row) == 2 and row[0] == 1 and isinstance(row[1], str):
            chunks.append(row[1])
    records = {}
    for line in "".join(chunks).splitlines():
        key, _, value = line.partition(":")
        if key in ("c1", "103"):
            if key in records:
                raise ValueError("Duplicate locale record")
            records[key] = json.loads(value)
    if set(records) != {"c1", "103"} or any(row.get("locale") != "en" for row in records.values()):
        raise ValueError("Expected captured English c1 and 103 locale records")
    cup = records["103"]["resources"]["web"]["leaderboard"]["cup"]
    result = {key: cup["rules"][key] for key in RULE_KEYS}
    result.update({key: cup[key] for key in CUP_KEYS})
    result["close"] = records["c1"]["resources"]["common"]["close"]
    if any(not isinstance(value, str) or not value for value in result.values()):
        raise ValueError("Missing captured rule label")
    return result


def generate(root):
    manifest = json.loads((root / "evidence/web/manifest.json").read_text(encoding='utf-8'))
    rows = [r for r in manifest["records"] if r.get("url") == "https://pump.fun/leaderboard"]
    if manifest["captured_at"] != "2026-10-28T10:48:45.546100+00:00" or len(rows) != 1:
        raise ValueError("Unexpected capture checkpoint")
    expected = {"path": SOURCE, "bytes": 365706, "sha256": SHA256, "status": 200, "final_url": "https://pump.fun/leaderboard"}
    if any(rows[0].get(key) != value for key, value in expected.items()):
        raise ValueError("Locale manifest identity differs")
    raw = (root / SOURCE).read_bytes()
    if len(raw) != 365706 or hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("Locale bytes differ")
    return json.dumps(extract(raw.decode("utf-8", errors="strict")), ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = generate(args.root)
    output = args.root / OUTPUT
    if args.check:
        if output.read_text(encoding='utf-8') != expected:
            raise SystemExit("Competition rules copy differs from retained HTML JSON")
        print("Verified 32 captured competition rules labels; no JavaScript executed")
    else:
        output.write_text(expected, encoding='utf-8', newline='\n')
