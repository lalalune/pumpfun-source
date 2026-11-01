#!/usr/bin/env python3
"""Exercise the maintained source-pinned wrapper using actual captured programs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

WRAPPER = 'research/tooling-analysis-output-retention-20261029/generate.py'
HELPERS = ('scripts/analyze_program.py', 'scripts/deep_disassembly.py',
           'scripts/window_elf_reader.py')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hashes(directory):
    return {p.name: digest(p.read_bytes()) for p in directory.iterdir()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    root = args.repository.resolve()
    sources = {name: subprocess.check_output(['git', '-C', str(root), 'show',
        args.revision + ':' + name]) if args.revision else (root/name).read_bytes()
        for name in (*HELPERS, WRAPPER)}
    evidence = {p.relative_to(root).as_posix(): p.read_bytes()
                for p in (root/'evidence').rglob('*') if p.is_file()}
    rows, controls = [], []
    with tempfile.TemporaryDirectory(prefix='manifest-wrapper-proof-') as temporary:
        workspace = Path(temporary)
        cohort = workspace/'source'
        for name, data in {**sources, **evidence}.items():
            path = cohort/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        def run(script, program, output):
            return subprocess.run([sys.executable, '-I', '-B', str(cohort/script),
                '--program', program, '--output', str(output)], cwd=cohort,
                capture_output=True, text=True, timeout=120)

        for program in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            direct, wrapped = workspace/(program+'-direct'), workspace/(program+'-wrapped')
            a = run(HELPERS[0], program, direct)
            b = run(WRAPPER, program, wrapped)
            assert a.returncode == b.returncode == 0, (program, a.stderr, b.stderr)
            assert hashes(direct) == hashes(wrapped)
            payload = hashes(wrapped)
            del payload['manifest.json'], payload['verify.py']
            rows.append({'program': program, 'direct_exit': a.returncode,
                         'wrapper_exit': b.returncode, 'all_packet_bytes_identical': True,
                         'analysis_payload_sha256': payload})
        for name in HELPERS:
            path = cohort/name
            path.write_bytes(sources[name]+b'\n# unreviewed source drift\n')
            output = workspace/'rejected'
            result = run(WRAPPER, 'mayhem', output)
            assert result.returncode == 1 and 'Unreviewed analysis helper' in result.stderr
            assert not output.exists()
            path.write_bytes(sources[name])
            controls.append({'case': name, 'exit': result.returncode, 'published': False})
        for kind in ('file', 'empty_directory'):
            output = workspace/kind
            if kind == 'file':
                output.write_bytes(b'prior packet')
            else:
                output.mkdir()
            result = run(WRAPPER, 'mayhem', output)
            assert result.returncode == 1 and 'already exists' in result.stderr
            assert output.read_bytes() == b'prior packet' if kind == 'file' else list(output.iterdir()) == []
            controls.append({'case': kind, 'exit': result.returncode, 'preserved': True})
        assert all((cohort/name).read_bytes() == data for name, data in {**sources, **evidence}.items())
    assert all((root/name).read_bytes() == data for name, data in evidence.items())
    if not args.revision:
        assert all((root/name).read_bytes() == data for name, data in sources.items())
    result = {'source_revision': args.revision or subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': {name: digest(data) for name, data in sources.items()},
        'programs': rows, 'controls': controls, 'inputs_unchanged': True}
    if args.compare:
        previous = json.loads(args.compare.read_text())
        assert previous['programs'] == rows
        assert previous['controls'] == controls
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'actual_cli_calls': 13, 'inputs_unchanged': True}))


if __name__ == '__main__':
    main()
