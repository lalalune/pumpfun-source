#!/usr/bin/env python3
"""Run unchanged SBPF tooling checks on sealed historical sources, then current Mayhem."""
if not __debug__: raise SystemExit("Normal Python is required; do not use -O.")
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HISTORY = Path('repro/build-tooling/supported-sbpf-integration')
HISTORY_SEAL = '45753774bd4cf003d94aef7a1f19114639833fb435992c36fd0a7894837e3182'
HISTORY_VERIFIER = 'b9ac7844605bfe5a48328e08f1d655b21dddd5ae6aa8ce93ba1eb3b536a7bf5b'
PROPOSAL = Path('repro/build-tooling/supported-sbpf-proposal')
PROPOSAL_SEAL = 'edac5debf5d734e2eb5968fd0c6526196cce91256b182d1d3d43bedadf8e0042'
TRANSITION = Path('repro/build-tooling/supported-sbpf-transition-20261029')
TRANSITION_SEAL = '9346126280488466b5b71def18d06e03f311626d7e39bc197246c0f773da9bbf'
CURRENT = Path('repro/mayhem/initializer-current-20261027')
CURRENT_SEAL = 'b6b01b400fb7c5ab10db803ba27fe6a76e0e59e9ea7fad25250dc95760cf485c'
CURRENT_CANDIDATE = '8dac1ff7575e3aa74ffa1ab4c4db2152781f0c644665dbf1c278e284751b19cb'
SOURCE14 = {
    'programs/mayhem/Cargo.lock': '03c991d636c42f72dda4e72e7aa5344ae8cba80aff672ec601d7176e596049b3',
    'programs/mayhem/Cargo.toml': '7745554bb59a2ba6d4daae31ccebcda50a75bcdba23251fe73a42e0c11fb7967',
    'programs/mayhem/src/checked_program.rs': 'fbf8eeaec04bc5ac5534b4a375f221fd8c3787a9a443e63d332ecc0a6395b7fb',
    'programs/mayhem/src/instructions/burn.rs': 'cb287a0009a1195efd5bdac08c5042a26dfc68d71a9a46c54c275453a11fd367',
    'programs/mayhem/src/instructions/buy.rs': '10a99ac5097a2cd8faee56a1a7baa3a8115c59baf37737f1c1336febb1693bf0',
    'programs/mayhem/src/instructions/buy_pump_swap.rs': 'd824aa4129b4645ac4e60fe9a0f9d827f173965c9dec1e631114ec076bff0801',
    'programs/mayhem/src/instructions/buy_v2.rs': 'e76d57d6eca28de9c1164a856ce15f303bf160f5920f31a63ac34b4598255daf',
    'programs/mayhem/src/instructions/mod.rs': 'da69605543cf37e3508c931529df76b4319755f73ec10c6110c3b5f2419cce4c',
    'programs/mayhem/src/instructions/pump_swap_types.rs': '9c37cb187c6225fdd6ef4f521f2ac6d794598828e7594b20628cd05631c129d5',
    'programs/mayhem/src/instructions/sell.rs': 'fd9263e97aa01f3394165297844286509094d87f38019c5df7c4a4e64b4fef64',
    'programs/mayhem/src/instructions/sell_pump_swap.rs': '2bf58880030a7859b8eaafcef3ddfde9ae0d7769a01c7dc54d8ba6805d1def31',
    'programs/mayhem/src/instructions/sell_v2.rs': 'e7b64a1f67e13026b6962a5fc229e39546939d0e701e9d4d1d6114713aea5f15',
    'programs/mayhem/src/lib.rs': 'def14c8135f370f8657b327c2bc2da3f8802ef3223778ad29b51958ba89c3649',
    'programs/mayhem/src/state.rs': '6da988a2efbf673e87465a21f38fe0b42b919948fe34c552755d02ee352658f2',
}
REFERENCES = {
    'repro/identity-audit/2026-10-25/mayhem-v154/build-01/candidate.so': 'ca5d4f54b14e2f67c4eca56fcac29b54801906cecf23c463801916fd9d6b6621',
    'evidence/original/mayhem/deployed.so': 'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    path = Path(value)
    assert not path.is_absolute() and '..' not in path.parts and path.parts, value
    return path


def authenticated(root, name, digest):
    path = root / relative(name)
    for part in [path, *path.parents]:
        if part == root.parent:
            break
        assert not part.is_symlink(), part
    data = path.read_bytes()
    assert sha(data) == digest, name
    return data


def write(view, name, data):
    path = view / relative(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), path
    path.write_bytes(data)


def stage_package(root, view, package, seal):
    raw = authenticated(root, package / 'manifest.json', seal)
    manifest = json.loads(raw)
    actual = {p.relative_to(root / package).as_posix() for p in (root / package).rglob('*')
              if p.is_file() and p != root / package / 'manifest.json' and '__pycache__' not in p.parts}
    assert actual == set(manifest), package
    write(view, package / 'manifest.json', raw)
    for name, digest in manifest.items():
        part = package / relative(name)
        write(view, part, authenticated(root, part, digest))


def stage_historical_view(root, view):
    """Copy authenticated bytes only; no current Mayhem source is substituted."""
    authenticated(root, HISTORY / 'verify.py', HISTORY_VERIFIER)
    stage_package(root, view, HISTORY, HISTORY_SEAL)
    stage_package(root, view, PROPOSAL, PROPOSAL_SEAL)
    attempt = json.loads((view / HISTORY / 'build-attempt.json').read_bytes())
    assert attempt['source_sha256'] == SOURCE14
    for name, digest in SOURCE14.items():
        write(view, name, authenticated(root, HISTORY / 'source' / name, digest))
    installed = json.loads((view / HISTORY / 'installed-files.json').read_bytes())
    for name, digest in installed.items():
        write(view, name, installed_historical_bytes(root, name, digest))
    for name, digest in REFERENCES.items():
        write(view, name, authenticated(root, name, digest))
    return len(installed)


def transition(root):
    raw = authenticated(root, TRANSITION / 'manifest.json', TRANSITION_SEAL)
    manifest = json.loads(raw)
    actual = {p.relative_to(root / TRANSITION).as_posix() for p in (root / TRANSITION).rglob('*') if p.is_file()}
    assert actual == set(manifest) | {'manifest.json'}, 'transition inventory'
    for name, digest in manifest.items():
        authenticated(root, TRANSITION / relative(name), digest)
    record = json.loads((root / TRANSITION / 'transition.json').read_bytes())
    assert set(record['entries']) == {'scripts/build_supported_sbpf_candidate.py', 'scripts/build_source_manifest.py'}
    historical_manifest = json.loads(authenticated(root, HISTORY / 'manifest.json', HISTORY_SEAL))
    installed = json.loads(authenticated(root, HISTORY / 'installed-files.json', historical_manifest['installed-files.json']))
    for name, entry in record['entries'].items():
        before = historical_helper(root, name, installed[name])
        after = authenticated(root, TRANSITION / relative(entry['after_file']), entry['after_sha256'])
        assert authenticated(root, name, entry['after_sha256']) == after, name
        assert entry['before_sha256'] == installed[name]
        diff = ''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True), fromfile='historical/' + name, tofile='current/' + name))
        assert diff == (root / TRANSITION / entry['diff_file']).read_text(), name
    assert set(record['policy_tests']) == {'scripts/test_supported_sbpf_policy.py', 'scripts/test_supported_sbpf_entry_paths.py'}
    for name, expected in record['policy_tests'].items():
        authenticated(root, name, expected['sha256'])
    return record


def historical_helper(root, name, expected):
    if name == 'scripts/build_source_manifest.py':
        raw = (root / PROPOSAL / 'historical/build_source_manifest.py').read_bytes()
    elif name == 'scripts/build_supported_sbpf_candidate.py':
        old = (root / HISTORY / 'adapter-at-build.py').read_text()
        block = (root / HISTORY / 'preflight-hardening-block.txt').read_text()
        assert old.count('    for name in sources:\n') == 1
        raw = old.replace('    for name in sources:\n', block + '    for name in sources:\n').encode()
    else:
        raise AssertionError('unreviewed historical helper transition: ' + name)
    assert sha(raw) == expected, name
    return raw


def installed_historical_bytes(root, name, expected):
    path = root / relative(name)
    assert path.is_file() and not path.is_symlink(), name
    raw = path.read_bytes()
    if sha(raw) == expected:
        return raw
    assert (root / TRANSITION / 'manifest.json').is_file(), 'unreviewed installed helper change: ' + name
    record = transition(root)
    assert name in record['entries'], 'unreviewed installed helper change: ' + name
    return historical_helper(root, name, expected)


def run_json(command, cwd):
    # Capture only stdout (parsed below); a failing command keeps its stderr in the log.
    result = subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return json.loads(result.stdout)


def verify(root):
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix='supported-sbpf-history-') as temporary:
        view = Path(temporary)
        installed_count = stage_historical_view(root, view)
        historical = run_json([sys.executable, '-B', str(view / HISTORY / 'verify.py')], view)
    assert historical['verified'] and historical['unchanged_source_inputs'] == 14
    assert historical['accepted_checkpoint_promoted'] is False and historical['new_runtime_executions'] == 0
    reviewed = transition(root)
    policy_tests = {}
    for name, expected in reviewed['policy_tests'].items():
        result = subprocess.run([sys.executable, '-B', str(root / name)], cwd=root, capture_output=True, text=True)
        assert result.returncode == 0 and ('Ran ' + str(expected['expected_tests']) + ' tests') in result.stderr and '\nOK\n' in result.stderr, result.stdout + result.stderr
        policy_tests[name] = expected['expected_tests']
    owner = reviewed['current_Mayhem']
    selected = json.loads((root / 'repro/status.json').read_bytes())['mayhem']
    assert selected['candidate_artifact'] == owner['candidate_artifact'] and selected['candidate_sha256'] == owner['candidate_sha256'], 'actual selected Mayhem'
    assert selected['checkpoint_manifest_sha256'] == owner['checkpoint_manifest_sha256'] and selected['source_identity_report_sha256'] == owner['selection_sha256'], 'current owning selection'
    authenticated(root, owner['bridge'], owner['bridge_sha256'])
    current = run_json([sys.executable, '-B', str(root / owner['bridge']), '--repo', str(root)], root)
    assert current['status'] == 'PASS' and current['candidate_sha256'] == selected['candidate_sha256'] and current['current_source_verified'] is True
    assert current['meaningful_elf_equal'] is True
    # The previous initializer is retained strictly as historical evidence.
    authenticated(root, CURRENT / 'candidate.so', CURRENT_CANDIDATE)
    authenticated(root, CURRENT / 'manifest.json', CURRENT_SEAL)
    return {'status': 'PASS', 'historical_verifier_sha256': HISTORY_VERIFIER,
            'historical_manifest_sha256': HISTORY_SEAL, 'historical_source_files': len(SOURCE14),
            'authenticated_installed_files': installed_count, 'historical': historical,
            'installed_transition_manifest_sha256': TRANSITION_SEAL, 'actual_synthetic_policy_tests': policy_tests,
            'historical_initializer': {'candidate_sha256': CURRENT_CANDIDATE, 'manifest_sha256': CURRENT_SEAL, 'is_current_selection': False},
            'current': current, 'sealed_packets_modified': False, 'current_sources_modified': False,
            'new_compiler_or_VM_executions': 0}



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo), indent=2))
