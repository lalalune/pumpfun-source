"""Run real AMM staging regressions and retain their actual process output."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if not shutil.which('rsync'):
    raise SystemExit('real rsync is required; a skipped proof is not success')
out = ROOT / 'work/scoped-proof'
out.mkdir(parents=True, exist_ok=True)
command = [sys.executable, '-B', str(ROOT / 'tests/test_amm_lane_baseline.py'), '-v']
result = subprocess.run(command, capture_output=True, text=True)
(out / 'staging-tests.log').write_text(result.stdout + result.stderr, encoding='utf-8')
(out / 'result.json').write_text(json.dumps({'command': command, 'returncode': result.returncode,
    'scope': 'Real staged repository Rust, actual rsync; stop at absent compiler boundary, no compiler result claimed'}, indent=2) + '\n')
print(result.stdout + result.stderr)
if result.returncode:
    raise SystemExit(result.returncode)
for name in ('test_native_build_preservation.py', 'test_workspace_recipe_staging.py'):
    check = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/amm_sell' / name)],
                           capture_output=True, text=True)
    (out / (name + '.log')).write_text(check.stdout + check.stderr, encoding='utf-8')
    print(check.stdout + check.stderr)
    if check.returncode:
        raise SystemExit(check.returncode)
