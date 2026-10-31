"""Stage the real production module closure for isolated analyzer regressions."""
from pathlib import Path
import shutil
import os
from contextlib import contextmanager


@contextmanager
def directory_link(target, link):
    """Owned directory alias without requiring Windows symlink privilege."""
    link = Path(link)
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)
    try:
        yield link
    finally:
        if os.name == 'nt': os.rmdir(link)
        else: link.unlink()


def copy_harness_modules(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(Path(__file__).resolve().parent.glob('*.py')):
        if not source.name.startswith('test_'):
            shutil.copyfile(source, destination / source.name)
