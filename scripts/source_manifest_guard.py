"""Reject symlinked compiler inputs before a source manifest is trusted.

`build_source_manifest.source_manifest` intentionally records `path -> sha256`
for local inputs. `Path.rglob` plus `is_file()` follows symlinks, so a symlinked
`.rs` can be recorded under an in-repo name while its bytes live outside the
repository. This module keeps the archived helper unchanged and adds the
admission check used by the production Pump build verifier.
"""
import os
from pathlib import Path

from build_source_manifest import source_manifest


def _plain(path, root):
    """Reject a symlink at `path` or in its ancestry below `root`.

    Raises before resolving an outside path, so a path outside the repository
    cannot walk to the filesystem root or loop forever.
    """
    path = Path(path)
    root = Path(root).resolve()
    current = path
    if not current.is_absolute():
        current = root / current
    try:
        current.relative_to(root)
    except ValueError:
        raise ValueError('compiler input resolves outside repository: ' + str(path))
    while True:
        if current.is_symlink():
            raise ValueError('symlinked compiler input: ' + str(path))
        if current == root:
            break
        parent = current.parent
        if parent == current:
            raise ValueError('compiler input resolves outside repository: ' + str(path))
        current = parent
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('compiler input resolves outside repository: ' + str(path))
    return resolved


def _no_linked_directories(top):
    """Reject a symlinked directory anywhere below `top`.

    `Path.rglob('*')` does not descend into symlinked directories, so files
    behind one never reach the manifest and `_plain` never sees them, while
    the compiler still reads them through the link.
    """
    top = Path(top)
    for directory, names, _ in os.walk(top):
        if Path(directory) == top:
            names[:] = [name for name in names if name not in ('target', '.git')]
        for name in names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError('symlinked directory under compiler inputs: ' + str(path))


def strict_manifest(crate, workspace, repository, extra_inputs=(), cwd=None):
    """Return the archived manifest after rejecting symlinked or outside inputs."""
    root = Path(repository).resolve()
    crate_path, workspace_path = Path(crate).resolve(), Path(workspace).resolve()
    _no_linked_directories(crate_path)
    for directory in (crate_path, *crate_path.parents):
        _no_linked_directories(directory / 'idls')
        if directory == workspace_path:
            break
    for extra in extra_inputs:
        extra_path = Path(extra)
        if not extra_path.is_absolute():
            extra_path = root / extra_path
        _plain(extra_path, root)
        if extra_path.is_dir():
            _no_linked_directories(extra_path)
            for path in extra_path.rglob('*'):
                if path.is_file():
                    _plain(path, root)
    return source_manifest(
        crate,
        workspace,
        repository,
        extra_inputs,
        cwd=cwd,
        before_read=lambda path: _plain(path, root),
    )
