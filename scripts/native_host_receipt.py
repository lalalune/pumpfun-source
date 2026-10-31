"""Bind a native comparison receipt to a host unchanged across its execution."""
import hashlib
from pathlib import Path
import subprocess


def run_host(path, **kwargs):
    """Return the process and pre-run digest; refuse an observed host replacement.

    These endpoint checks detect a rebuild during execution, not a replacement
    followed by restoration between checks. They do not prove a source build.
    """
    path = Path(path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = subprocess.run([str(path)], **kwargs)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('native host changed during execution: ' + str(path))
    return result, digest
