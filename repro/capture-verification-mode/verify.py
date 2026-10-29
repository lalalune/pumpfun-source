"""Run the frozen saved-capture verifier with all of its assertions enabled."""
import pathlib
import runpy
import sys

if not __debug__:
    raise SystemExit('Capture verification requires assertions: rerun without -O/-OO and unset PYTHONOPTIMIZE.')

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
runpy.run_path(str(ROOT / 'scripts/verify_evidence.py'), run_name='__main__')
