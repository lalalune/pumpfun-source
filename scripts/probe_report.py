"""Helpers for durable JSON reports from local probe scripts."""
import json
import os
from pathlib import Path
import tempfile


def write_json_report(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            prefix="." + path.name + ".",
            delete=False,
            encoding="utf-8",
            newline="\n",
        ) as stream:
            staged = Path(stream.name)
            stream.write(json.dumps(value, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, path)
    except BaseException:
        if staged is not None:
            staged.unlink(missing_ok=True)
        raise
