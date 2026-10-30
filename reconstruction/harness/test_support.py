"""Stage the real production module closure for isolated analyzer regressions."""
from pathlib import Path
import shutil


def copy_harness_modules(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(Path(__file__).resolve().parent.glob('*.py')):
        if not source.name.startswith('test_'):
            shutil.copyfile(source, destination / source.name)
