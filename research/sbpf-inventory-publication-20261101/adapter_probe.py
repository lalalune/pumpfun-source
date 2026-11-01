#!/usr/bin/env python3
"""Exercise the maintained section-name adapter with real retained disassembly."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from reproduce import packet

BASE = '1647da0f22312730b2e6b3eec7a468d9d3d89041'
LEGACY = 'd07c6f6507bcf4e901bb9aefe4d93a58bd03a692'
WRAPPER = 'research/sbpf-section-name-admission/inventory.py'
GENERATOR = 'scripts/sbpf_disassembly_inventory.py'
TOOL_REVISION = '422a6316cbb1ac60b07b60a555bfbcb8e557bcef'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--tool-source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, tool = args.repository.resolve(), args.tool_source.resolve()

    def git_source(revision, path):
        return subprocess.check_output(['git', '-C', str(root), 'show', revision + ':' + path])

    assert subprocess.check_output(['git', '-C', str(tool), 'rev-parse', 'HEAD'],
        text=True).strip() == TOOL_REVISION
    sources = {name: (root / name).read_bytes() for name in (
        GENERATOR, 'scripts/analyze.py', 'scripts/deep_disassembly.py',
        'scripts/window_elf_reader.py', WRAPPER)}
    captures = {p.relative_to(root).as_posix(): p.read_bytes()
                for p in sorted((root / 'evidence').glob('**/deployed.so'))}
    assert len(captures) == 9
    executable = tool / 'target/release/sbpf'
    tool_digest = sha(executable.read_bytes())
    old_wrapper = git_source(BASE, WRAPPER)
    legacy_generator = git_source(LEGACY, GENERATOR)
    assert sha(legacy_generator) == '08070b3ea6c8e5627a85c8d53bd63fc6fc25b2534f1da9fd82e0adce6a59013f'
    assert sha(sources[GENERATOR]) == '0d3714567123a34fd504b97609d00bd1a61eb223213d8b2dc39af68a61081bcf'
    cases = (
        ('before-current-generator', old_wrapper, sources[GENERATOR], False, WRAPPER),
        ('after-current-generator', sources[WRAPPER], sources[GENERATOR], True, WRAPPER),
        ('historical-admitted-control', old_wrapper, legacy_generator, True, WRAPPER),
        ('reject-unreviewed-generator', sources[WRAPPER],
         sources[GENERATOR] + b'\nraise RuntimeError("unreviewed source executed")\n', False, WRAPPER),
        ('reject-previous-generator', sources[WRAPPER], legacy_generator, False, WRAPPER),
        ('direct-current-control', sources[WRAPPER], sources[GENERATOR], True, GENERATOR),
    )
    results = []
    with tempfile.TemporaryDirectory(prefix='section-name-adapter-proof-') as temporary:
        workspace = Path(temporary)
        for label, wrapper, generator, succeeds, entrypoint in cases:
            cohort = workspace / label
            admitted = dict(sources, **{WRAPPER: wrapper, GENERATOR: generator})
            for name, data in {**admitted, **captures}.items():
                path = cohort / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            output = cohort / 'packet'
            run = subprocess.run([sys.executable, '-B', str(cohort / entrypoint),
                '--tool-source', str(tool), '--output', str(output)], cwd=cohort,
                capture_output=True, text=True, timeout=120)
            assert (run.returncode == 0) == succeeds, (label, run.stderr)
            record = packet(output)
            assert (record is not None) == succeeds, label
            if succeeds:
                assert record['generator_sha256'] == sha(admitted[entrypoint])
                assert len(record['programs']) == 9
                assert sum(row['instruction_count'] for row in record['programs']) == 788302
            else:
                assert 'archived disassembly inventory source drift' in run.stderr
                assert 'unreviewed source executed' not in run.stderr
                assert not output.exists()
            assert all((cohort / name).read_bytes() == data
                       for name, data in {**admitted, **captures}.items())
            assert not list(cohort.glob('.packet.*'))
            results.append({'case': label, 'exit': run.returncode,
                'wrapper_sha256': sha(wrapper), 'generator_sha256': sha(generator),
                'source_and_capture_bytes_unchanged': True, 'packet': record,
                'source_drift_rejected': not succeeds})
    normal = results[1]['packet']
    historical = results[2]['packet']
    direct = results[5]['packet']
    for control in (historical, direct):
        assert normal['payload_sha256'] == control['payload_sha256']
        assert normal['semantic_manifest_sha256'] == control['semantic_manifest_sha256']
        assert normal['programs'] == control['programs']
    assert all((root / name).read_bytes() == data for name, data in sources.items())
    assert all((root / name).read_bytes() == data for name, data in captures.items())
    assert sha(executable.read_bytes()) == tool_digest
    result = {'base': BASE, 'legacy_generator_revision': LEGACY,
        'tool_revision': TOOL_REVISION, 'tool_sha256': tool_digest,
        'capture_count': len(captures), 'all_inputs_unchanged': True,
        'normal_payload_files_identical': 27, 'semantic_manifest_unchanged': True,
        'cases': results}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([{key: value for key, value in row.items() if key != 'packet'}
                      for row in results], indent=2))


if __name__ == '__main__':
    main()
