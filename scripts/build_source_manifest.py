"""Hash local Rust, workspace, Anchor IDL and explicitly supplied build inputs.

This inventories known local inputs, not a hermetic dependency/toolchain closure.
Pass external path dependencies or other include/build-script assets explicitly.
"""
import hashlib
from pathlib import Path


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(128 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_manifest(crate, workspace, repository, extra_inputs=(), cwd=None, before_read=None):
    crate, workspace, repository = map(lambda p: Path(p).resolve(), (crate, workspace, repository))
    cwd = Path(cwd or repository).resolve()
    crate.relative_to(workspace)
    workspace.relative_to(repository)
    files = {
        p for p in crate.rglob('*')
        if p.is_file() and not {'target', '.git'}.intersection(p.relative_to(crate).parts)
        and (p.suffix == '.rs' or p.name in ('Cargo.toml', 'Cargo.lock'))
    }
    for name in ('Cargo.toml', 'Cargo.lock'):
        p = workspace / name
        if p.is_file():
            files.add(p)
    # declare_program! searches ancestor idls directories, not just src/.
    for directory in (crate, *crate.parents):
        files.update(p for p in (directory / 'idls').glob('**/*.json') if p.is_file())
        if directory == workspace:
            break
    # Cargo config lookup starts from its invocation directory; record repository
    # configs and toolchain selectors without copying external credential stores.
    for start in (crate, cwd):
        start.relative_to(repository)
        for directory in (start, *start.parents):
            for name in ('.cargo/config', '.cargo/config.toml', 'rust-toolchain', 'rust-toolchain.toml'):
                p = directory / name
                if p.is_file():
                    files.add(p)
            if directory == repository:
                break
    for extra in extra_inputs:
        p = Path(extra).resolve()
        p.relative_to(repository)
        if not p.exists():
            raise FileNotFoundError(p)
        if p.is_file():
            files.add(p)
        else:
            files.update(f for f in p.rglob('*') if f.is_file() and not {'target', '.git'}.intersection(f.relative_to(p).parts))
    manifest = {}
    for path in sorted(files):
        if before_read is not None:
            before_read(path)
        manifest[path.relative_to(repository).as_posix()] = file_digest(path)
    return manifest
