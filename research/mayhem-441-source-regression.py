#!/usr/bin/env python3
"""Small source-level regression guard for the merged Mayhem 441 recovery.

This intentionally does not claim binary equivalence. It protects the source
routing that was used to close O0083/O0084: the v2 handlers live in the shared
pump_interface_v2 module and the obsolete standalone BuyV2 handler is absent.

Run from the repository root:
    python -B research/mayhem-441-source-regression.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "programs/mayhem/src/instructions/pump_interface_v2.rs"
BUY = ROOT / "programs/mayhem/src/instructions/buy_v2.rs"


def require_pattern(path: Path, pattern: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not re.search(pattern, text):
        raise SystemExit(f"missing pattern {pattern!r} in {path}")


def forbid_pattern(path: Path, pattern: str) -> None:
    text = path.read_text(encoding="utf-8")
    if re.search(pattern, text):
        raise SystemExit(f"unexpected pattern {pattern!r} in {path}")


require_pattern(V2, r"\bpub\s+fn\s+buy_v2_handler\s*\(")
require_pattern(V2, r"\bpub\s+fn\s+sell_v2_handler\s*\(")
require_pattern(V2, r"\bif\s+native\s*\{")
require_pattern(V2, r"emit_cpi!\s*\(\s*event\s*\)")
forbid_pattern(BUY, r"\bpub\s+fn\s+handler\s*\(\s*ctx\s*:\s*Context\s*<\s*BuyV2\s*>\s*\)")

print("Mayhem 441 source regression checks: PASS")
