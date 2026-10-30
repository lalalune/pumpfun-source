"""Real native AMM CLI cache admission, with genuine compiler/ELF evidence."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SWARM = ROOT / 'work/actual-amm-cache-swarm'
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
HYBRID = Path.home() / '.cache/pumpfun-reconstruction/toolchains/hybrid144'
spec = importlib.util.spec_from_file_location('actual_workspace_recipe', ROOT / 'scripts/amm_sell/workspace_recipe.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
SWARM.mkdir()
native = SWARM / 'infra/sdk-native'
native.parent.mkdir(parents=True)
subprocess.run(['cp', '-cR', str(SDK), str(native)], check=True)
target_libs = native / 'rust/lib/rustlib/sbpf-solana-solana'
if target_libs.exists():
    shutil.rmtree(target_libs)
shutil.copytree(HYBRID / 'rust/lib/rustlib/sbpf-solana-solana', target_libs)
original = SWARM / 'infra/original/deployed.so'
original.parent.mkdir()
shutil.copyfile(ROOT / 'evidence/original/pump_amm/deployed.so', original)
pristine = SWARM / 'baselines/pristine-ws'
recipe.stage(ROOT, pristine)
env = dict(os.environ, AMM_SELL_SWARM=str(SWARM), CARGO_HOME=str(SWARM / 'infra/cargo-home'),
           CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse', RUSTC=str(native / 'rust/bin/rustc'))
with (PROOF / 'fetch.log').open('w') as log:
    subprocess.run([str(native / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(pristine / 'Cargo.toml')], env=env, cwd=pristine,
                   stdout=log, stderr=subprocess.STDOUT, timeout=300, check=True)


def attempt(name, lane, extra=()):
    result = subprocess.run([sys.executable, '-B', 'scripts/amm_sell/try_sell.py',
                             '--lane', lane, '--approach', 'real-cache-admission',
                             '--hypothesis', 'Same actual build inputs must reuse only intact evidence',
                             '--baseline', *extra], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=900)
    (PROOF / (name + '.stdout')).write_text(result.stdout)
    (PROOF / (name + '.stderr')).write_text(result.stderr)
    if result.returncode not in (0, 3):
        for log in SWARM.glob('lanes/**/build.log'):
            shutil.copyfile(log, PROOF / (name + '-build.log'))
        raise RuntimeError(f'{name}: real AMM build/score did not succeed ({result.returncode})')
    return json.loads(result.stdout)


first = attempt('first', 'control')
assert not first.get('duplicate') and first.get('candidate_sha256') and first.get('unstripped_sha256')
out = Path(first['out_dir'])
for name in ('build.log', 'build-record.json'):
    shutil.copyfile(out / name, PROOF / ('first-' + name))
for name in ('candidate.so', 'symbols.so'):
    (PROOF / (name + '.gz')).write_bytes(gzip.compress((out / name).read_bytes(), mtime=0))
repeat = attempt('intact-repeat', 'control')
assert repeat.get('duplicate') and repeat['attempt_id'] == first['attempt_id']
disasm = attempt('requested-disasm', 'control', ['--disasm'])
disasm_ok = len(disasm.get('disasm') or []) == 3 and all(Path(p).is_file() for p in disasm['disasm'])
candidate = out / 'candidate.so'
preserved = candidate.with_suffix('.preserved')
candidate.rename(preserved)
try:
    missing = attempt('missing-candidate', 'missing-output-control')
    missing_ok = not missing.get('duplicate') and Path(missing['out_dir'], 'candidate.so').is_file()
finally:
    # The original evidence is always retained, even when a fix rebuilds this key.
    if candidate.exists():
        shutil.copyfile(candidate, PROOF / 'rebuilt-candidate.so')
    if not candidate.exists():
        preserved.rename(candidate)
changed = pristine / 'programs/pump-amm/src/lib.rs'
prior = changed.read_bytes()
changed.write_bytes(prior + b'\n// Isolated cache source inventory control.\n')
try:
    source_change = attempt('changed-nonsell-baseline', 'changed-source-control')
    source_ok = not source_change.get('duplicate') and source_change['key'] != first['key']
finally:
    changed.write_bytes(prior)
summary = {'actual_initial_status': first['status'],
           'actual_candidate_sha256': first['candidate_sha256'],
           'actual_unstripped_sha256': first['unstripped_sha256'],
           'intact_repeat_reuses_actual_attempt': repeat.get('duplicate') and repeat['attempt_id'] == first['attempt_id'],
           'requested_disasm_retained': disasm_ok,
           'missing_candidate_rebuilt': missing_ok,
           'changed_nonsell_source_gets_new_key': source_ok}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert disasm_ok and missing_ok and source_ok, 'cache reused stale inputs/outputs or omitted the requested actual listing'
