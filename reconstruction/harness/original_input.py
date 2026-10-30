"""Read the captured original in native and core.symlinks=false checkouts."""
from pathlib import Path
import shutil


# Git stores this exact symlink payload as a regular file on some checkouts.
# Do not interpret arbitrary text (or candidate binaries) as paths.
_LINK = b'../../evidence/original/pump/deployed.so'


def resolve_original(path):
    path = Path(path)
    if not path.is_symlink() and path.stat().st_size == len(_LINK):
        if path.read_bytes() == _LINK:
            target = path.parent / _LINK.decode('ascii')
            if not target.is_file():
                raise FileNotFoundError(f'captured original symlink target missing: {target}')
            return target.resolve()
    return path


def copy_original_inputs(base, destination):
    """Snapshot actual ELF bytes, so relocation cannot break a relative link."""
    base, destination = Path(base), Path(destination)
    shutil.copyfile(resolve_original(base / 'original.so'), destination / 'original.so')
    shutil.copyfile(base / 'functions.tsv', destination / 'functions.tsv')
