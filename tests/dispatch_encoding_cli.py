"""Test-only platform text default; executes the unmodified selected CLI."""
import builtins
import io
from pathlib import Path
import runpy
import sys


def controlled(original):
    def open_with_default(file, mode="r", buffering=-1, encoding=None,
                          errors=None, newline=None, closefd=True, opener=None):
        if "b" not in mode and encoding in (None, "locale"):
            encoding = "cp936"
        return original(file, mode, buffering, encoding, errors, newline, closefd, opener)
    return open_with_default


builtins.open = controlled(builtins.open)
io.open = controlled(io.open)
script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, str(Path(script).resolve().parent))
runpy.run_path(script, run_name="__main__")
