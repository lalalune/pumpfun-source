"""Helpers for durable JSON reports from local probe scripts."""
import json
import os
from pathlib import Path
import secrets


def write_json_report(path, value, *, overwrite=True):
    """Publish JSON atomically; an optional fresh output never replaces a writer."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A plain exclusive open keeps the umask-derived mode of a direct write.
    # Include an unpredictable suffix so a stale file from a reused PID cannot
    # block a later publication.
    # Keep the readable prefix short: a valid output basename can already be
    # near the filesystem's component limit before the staging suffix is added.
    for _ in range(100):
        staged = path.with_name(
            "." + path.name[:32] + "." + str(os.getpid()) + "." + secrets.token_hex(8)
        )
        try:
            stream = open(staged, "x", encoding="utf-8", newline="\n")
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError("could not create a unique probe report staging file")
    metadata = os.fstat(stream.fileno())
    identity = metadata.st_dev, metadata.st_ino
    try:
        with stream:
            # NaN/Infinity are not JSON; refuse them instead of publishing
            # a report that strict JSON readers cannot parse.
            stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(staged, path)
            staged = None
        elif os.name == "nt":
            # Windows rename refuses an existing file without hard-link support.
            os.rename(staged, path)
            staged = None
        else:
            os.link(staged, path)
    finally:
        if staged is not None:
            try:
                metadata = staged.lstat()
            except FileNotFoundError:
                pass
            else:
                # A failed publisher may have lost its pathname to another
                # writer. Only remove the file allocated by this invocation.
                if (metadata.st_dev, metadata.st_ino) == identity:
                    staged.unlink()
