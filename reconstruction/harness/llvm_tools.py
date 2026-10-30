"""Resolve the analysis objdump independently of the compiler build recipe."""
import os
import shutil
from pathlib import Path


def objdump():
    explicit = os.environ.get('PUMP_OBJDUMP')
    if explicit is not None:
        resolved = shutil.which(explicit) if explicit else None
        if not resolved:
            raise FileNotFoundError('PUMP_OBJDUMP must name an executable llvm-objdump')
        return resolved
    for version in ('v1.52', 'v1.44'):
        candidate = Path.home() / '.cache/solana' / version / 'platform-tools/llvm/bin/llvm-objdump'
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    resolved = shutil.which('llvm-objdump')
    if resolved:
        return resolved
    raise FileNotFoundError('llvm-objdump not found; install the documented v1.44 SDK or set PUMP_OBJDUMP')
