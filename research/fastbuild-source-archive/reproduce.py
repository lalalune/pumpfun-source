"""Build real Pump output, then fail a rerun and verify old source provenance."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import fastbuild
import score

proof = ROOT / 'work/scoped-proof'
proof.mkdir(parents=True, exist_ok=True)
os.environ['CARGO_REGISTRIES_CRATES_IO_PROTOCOL'] = 'sparse'
os.environ['CARGO_BUILD_JOBS'] = '2'
fetch_env = {**os.environ, 'RUSTC': str(fastbuild.RECIPES['identity']['rustc']),
             'CARGO_HOME': str(Path.home() / '.cargo')}
subprocess.run([str(fastbuild.SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')],
               env=fetch_env, check=True)

with tempfile.TemporaryDirectory(prefix='pump-source-archive-', dir=ROOT / 'work') as temporary:
    trial = Path(temporary)
    work, out = trial / 'work', trial / 'out'
    fastbuild.LOCKDIR = trial / 'locks'
    fastbuild.RECIPES['identity'] = {**fastbuild.RECIPES['identity'], 'template': trial / 'absent-template'}
    first = fastbuild.build(ROOT / 'programs/pump', work, out, quiet=True, timeout=600)
    if not first.get('ok') or not first.get('runtime_valid') or first.get('stack_warnings'):
        shutil.copyfile(out / 'build.log', proof / 'first-build.log')
        raise RuntimeError('the real initial control build did not succeed')
    original_receipt = (out / 'source-inputs.json').read_bytes()
    original_link_artifacts = {name: (out / name).read_bytes()
                               for name in ('link-receipt.json', 'link.map')}
    if json.loads(original_receipt)['sha256'] != first['source_sha256']:
        raise RuntimeError('initial source receipt does not bind the real build')
    (proof / 'expected-prior-source-inputs.json').write_bytes(original_receipt)
    before_membership = score.score(out / 'unstripped.so')

    changed = trial / 'changed-source'
    shutil.copytree(ROOT / 'programs/pump', changed)
    source = changed / 'src/lib.rs'
    source.write_bytes(source.read_bytes() + b'\ncompile_error!("controlled failed provenance rerun");\n')
    second = fastbuild.build(changed, work, out, quiet=True, timeout=600)
    shutil.copyfile(out / 'build.log', proof / 'failed-rerun.log')
    if second.get('ok') or 'controlled failed provenance rerun' not in (out / 'build.log').read_text():
        raise RuntimeError('the controlled rerun did not reach its actual compiler diagnostic')
    archives = list((out / 'previous').iterdir())
    if len(archives) != 1:
        raise RuntimeError('expected one previous actual build')
    previous = archives[0]
    for name, expected in original_link_artifacts.items():
        if (previous / name).read_bytes() != expected:
            raise RuntimeError('prior genuine linker provenance changed: ' + name)
    for name in ('unstripped.so', 'candidate.so'):
        data = (previous / name).read_bytes()
        field = 'unstripped_sha256' if name == 'unstripped.so' else 'candidate_sha256'
        if hashlib.sha256(data).hexdigest() != first[field]:
            raise RuntimeError('prior real ELF changed')
        (proof / (name + '.gz')).write_bytes(gzip.compress(data, mtime=0))
    after_membership = score.score(previous / 'unstripped.so')
    if before_membership != after_membership or len(after_membership) != 1035:
        raise RuntimeError('archived actual ELF membership changed')
    new_receipt = (out / 'source-inputs.json').read_bytes()
    old_receipt = previous / 'source-inputs.json'
    summary = {'first_build': first, 'failed_rerun': second,
               'archive_files': sorted(p.name for p in previous.iterdir()),
               'new_receipt_differs': new_receipt != original_receipt,
               'prior_receipt_retained': old_receipt.is_file(),
               'prior_link_artifacts_preserved': True,
               'all_1035_memberships_preserved': before_membership == after_membership,
               'normalized': sum(v['normalized'] for v in after_membership.values()),
               'raw': sum(v['raw'] for v in after_membership.values())}
    (proof / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    if not old_receipt.is_file() or old_receipt.read_bytes() != original_receipt:
        raise AssertionError('the real prior ELF/log lost its original source-inputs.json on rerun')
    shutil.copyfile(old_receipt, proof / 'archived-source-inputs.json')
