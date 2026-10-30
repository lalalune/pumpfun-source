"""Helpers for durable JSON reports from local probe scripts."""
import json
import os
from pathlib import Path


def write_json_report(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name("." + path.name + "." + str(os.getpid()))
    # A plain exclusive open keeps the umask-derived mode of a direct write.
    stream = open(staged, "x", encoding="utf-8", newline="\n")
    try:
        with stream:
            stream.write(json.dumps(value, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, path)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
