#!/usr/bin/env python3
"""Qualify public staging and logical paths only; does not compile or run SDK tools."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import PACKAGE, digest, stage, validate_staged, write_new
from verify import verify

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['repo', 'sdk', 'registry', 'work', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise SystemExit('output exists; preserve the prior receipt')
    inputs = {n: digest(PACKAGE / n) for n in ['replay.py', 'stage.py', 'launch.py', 'prepare_sdk.py',
              'prepare_registry.py', 'verify.py', 'qualify_stage.py', 'test_replay.py', 'ARTIFACTS.json']}
    plan = stage(a.repo, a.sdk, a.registry, a.work)
    validate_staged(a.work)
    work = a.work.resolve(); target = work / 'target'; output = work / 'output'
    target.mkdir(); output.mkdir(); (output / 'home').mkdir()
    code = "from pathlib import Path; import json,hashlib,os; print(json.dumps({'cwd':str(Path.cwd()),'source':{p.relative_to(Path('/source')).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in Path('/source').rglob('*')if p.is_file()},'registryPackages':len(list(Path('/cargo/registry/src/index.crates.io-6f17d22bba15001f').glob('*/Cargo.toml'))),'hostCC':str(Path('/usr/bin/cc').resolve()),'targetEmpty':not any(Path('/target').iterdir()),'sdkHostLinkerPresent':Path('/sdk/rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld/ld.lld').is_file()}))"
    command = plan['argv']; cargo = command.index('/sdk/rust/bin/cargo')
    probe_command = command[:cargo] + ['/usr/bin/python3', '-c', code]
    try:
        result = subprocess.run(probe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    finally:
        (output / 'home').rmdir(); output.rmdir(); target.rmdir()
    observation = json.loads(result.stdout) if result.returncode == 0 else None
    packet = verify(a.repo)
    record = {'scope': 'New public stage/plan and metadata-only bwrap probe; no SDK tool/compile/build',
              'methodInputsBefore': inputs, 'methodInputsAfter': {n: digest(PACKAGE / n) for n in inputs},
              'argv': plan['argv'], 'probeArgv': probe_command, 'probeReturncode': result.returncode,
              'stdout': result.stdout.decode(), 'stderr': result.stderr.decode(), 'observation': observation,
              'packetVerification': packet, 'workPathContainsSpaces': ' ' in str(work),
              'freshCompileTargetAndOutputAbsentAfterProbe': not target.exists() and not output.exists(),
              'sdkExecutions': 0, 'sourceCompilations': 0,
              'prepareSdkAndRegistryHelpersExecutedToCompletion': False,
              'publicLaunchExecuteColdTested': False}
    write_new(a.output, record)
    if result.returncode or record['methodInputsBefore'] != record['methodInputsAfter']:
        raise SystemExit(1)
    expected = {r['path']: r['sha256'] for r in json.loads((PACKAGE / 'source-inputs.json').read_text())['files']}
    if observation['source'] != expected or observation['cwd'] != '/source' or observation['registryPackages'] != 253 or not observation['targetEmpty'] or not observation['sdkHostLinkerPresent']:
        raise SystemExit(1)
    print(json.dumps({'status': 'STAGING_AND_METADATA_ONLY_NAMESPACE_PASS', 'sourceFiles': 60,
                      'registryPackages': 253, 'compilerOrSdkExecutions': 0, 'output': str(a.output)}, indent=2))
