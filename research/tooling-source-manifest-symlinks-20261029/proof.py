"""Reject symlinked compiler inputs from the local source manifest.

`scripts/build_source_manifest.py` walks a crate with `Path.rglob`, accepts
`p.is_file()` (which follows symlinks), and returns only `path -> sha256`. A
symlinked `.rs` file inside the crate is therefore reported under its in-repo
path while its bytes come from outside the repository. The resulting record
cannot distinguish a local source from an external file, and a later copy step
would compile the external bytes under the local name.

`build_supported_sbpf_candidate.py` already rejects such entries explicitly.
This packet makes the same contract available for the archived helper without
editing it: the reviewed helper is loaded, its real-repository output is
compared unchanged, and a strict wrapper refuses symlinked inputs or symlinked
ancestors inside the repository.

`manifest_sha256` records the source-manifest identity at seal time.
`programs/pump` changes in independent reconstruction lanes, so the verifier
compares the guard's claims and keeps that hash as provenance for the sealed
revision instead of requiring live source bytes to match it forever.
"""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import types

P = Path(__file__).resolve().parent
REPO = next(
    parent for parent in P.parents
    if (parent / 'evidence/original/pump/deployed.so').is_file()
)
sys.path.insert(0, str(REPO / 'scripts'))
from source_manifest_guard import _plain, strict_manifest as production_strict  # noqa: E402

SOURCE = 'scripts/build_source_manifest.py'
LF_SHA256 = '05eb3446b95c0b7b80517fe05a98a9841fa53053fe39ca56fe2659daf6b58df0'
CLAIM_KEYS = ('scope', 'script', 'script_sha256', 'program', 'files', 'symlinks')
sha = lambda data: hashlib.sha256(data).hexdigest()


def claims(report):
    """Return the observation fields this packet asserts about the guard."""
    return {key: report[key] for key in CLAIM_KEYS}


def _reviewed(root=REPO):
    path = Path(root) / SOURCE
    raw = path.read_bytes()
    lf = raw.replace(b'\r\n', b'\n')
    forms = {sha(raw), sha(lf), sha(lf.replace(b'\n', b'\r\n'))}
    if LF_SHA256 not in forms:
        raise ValueError('the reviewed source-manifest helper has changed')
    module = types.ModuleType('reviewed_build_source_manifest')
    module.__file__ = str(path)
    exec(compile(lf, str(path), 'exec'), module.__dict__)
    return module


def strict_manifest(module, crate, workspace, repository, extra_inputs=(), cwd=None):
    """Check the reviewed helper against the production admission guard."""
    manifest = module.source_manifest(crate, workspace, repository, extra_inputs, cwd=cwd)
    production = production_strict(crate, workspace, repository, extra_inputs, cwd=cwd)
    assert manifest == production
    return production


def check(root=REPO):
    root = Path(root).resolve()
    module = _reviewed(root)
    crate = root / 'programs/pump'
    archived = module.source_manifest(crate, crate, root)
    strict = strict_manifest(module, crate, crate, root)
    assert archived == strict
    assert len(strict) == 65
    symlinks = [name for name in strict if (root / name).is_symlink()]
    assert symlinks == []
    return {
        'scope': 'Review and strict check of the local Pump source manifest; no build.',
        'script': SOURCE,
        'script_sha256': sha((root / SOURCE).read_bytes()),
        'program': 'pump',
        'files': len(strict),
        'symlinks': symlinks,
        'manifest_sha256': hashlib.sha256(
            json.dumps(strict, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest(),
    }


def seal(packet=P):
    packet = Path(packet)
    report = check(REPO)
    (packet / 'observations.json.gz').write_bytes(
        gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    )
    (packet / 'coverage-delta.json').write_text(
        json.dumps({
            'kind': 'tooling',
            'scope': 'Source-manifest symlink admission; no payload-byte claim.',
            'totals': {'files': report['files'], 'symlinks': len(report['symlinks'])},
        }, indent=2) + '\n'
    )
    inventory = {
        str(path.relative_to(packet)): sha(path.read_bytes())
        for path in sorted(packet.rglob('*'))
        if path.is_file() and path.name != 'manifest.json'
        and '__pycache__' not in path.parts and path.suffix != '.pyc'
    }
    (packet / 'manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(seal(), indent=2))
