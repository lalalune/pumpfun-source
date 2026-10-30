"""Helpers for durable JSON reports from local probe scripts."""
import json
from pathlib import Path


def write_json_report(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
