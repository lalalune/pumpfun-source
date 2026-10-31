"""Reject symlinked compiler inputs before a source manifest is trusted.

`build_source_manifest.source_manifest` intentionally records `path -> sha256`
for local inputs. `Path.rglob` plus `is_file()` follows symlinks, so a symlinked
`.rs` can be recorded under an in-repo name while its bytes live outside the
repository. This module keeps the archived helper unchanged and adds the
admission check used by the production Pump build verifier.
"""
import os
import stat
from pathlib import Path

from build_source_manifest import source_manifest


def _is_symlink_or_reparse(path):
    """Return true for symlinks and Windows reparse points such as junctions."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_reparse_tag', 0))


def _check_under_root(current, root, display_path):
    while True:
        if current == root:
            break
        if _is_symlink_or_reparse(current):
            raise ValueError('symlinked compiler input or reparse point: ' + str(display_path))
        parent = current.parent
        if parent == current:
            raise ValueError('compiler input resolves outside repository: ' + str(display_path))
        current = parent


def _plain(path, root):
    """Reject a link or reparse point at `path` or in its ancestry below `root`.

    The repository path itself may contain filesystem aliases, such as
    macOS's `/var` to `/private/var`.  Compare the resolved locations first,
    then inspect the equivalent lexical path below the caller's root so links
    inside the repository remain rejected.
    """
    path = Path(path)
    root = Path(os.path.abspath(root))
    resolved_root = root.resolve()
    raw = path if path.is_absolute() else root / path
    for lexical_root in (root, resolved_root):
        if raw.parts[:len(lexical_root.parts)] == lexical_root.parts:
            cursor = root
            for part in raw.parts[len(lexical_root.parts):]:
                if part == '..':
                    cursor = cursor.parent
                else:
                    cursor = cursor / part
                    if cursor != root and cursor.is_relative_to(root) and _is_symlink_or_reparse(cursor):
                        raise ValueError('symlinked compiler input or reparse point: ' + str(path))
            break
    current = Path(os.path.abspath(raw))
    for lexical_root in (root, resolved_root):
        try:
            current = root / current.relative_to(lexical_root)
            break
        except ValueError:
            continue
    else:
        resolved = current.resolve()
        try:
            current = root / resolved.relative_to(resolved_root)
        except ValueError:
            raise ValueError(
                'compiler input resolves outside repository: ' + str(path)
            ) from None
    _check_under_root(current, root, path)
    resolved = raw.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError('compiler input resolves outside repository: ' + str(path))
    _check_under_root(root / resolved.relative_to(resolved_root), root, path)
    return resolved


def _check_optional_directory(path):
    path = Path(path)
    if _is_symlink_or_reparse(path):
        raise ValueError('symlinked directory or reparse point under compiler inputs: ' + str(path))
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(f'cannot traverse compiler inputs under {path}: {error}') from error
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError('non-regular compiler input: ' + str(path))


def _check_optional_input_file(path):
    path = Path(path)
    if _is_symlink_or_reparse(path):
        raise ValueError('symlinked compiler input or reparse point: ' + str(path))
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(f'cannot traverse compiler inputs under {path}: {error}') from error
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('non-regular compiler input: ' + str(path))


def _no_linked_directories(top, *, optional=False):
    """Reject a linked directory, broken link, reparse point, or special file below `top`.

    `Path.rglob('*')` does not descend into symlinked directories, so files
    behind one never reach the manifest and `_plain` never sees them, while
    the compiler still reads them through the link. Dangling symlinks and
    special files (such as FIFOs) are also omitted by `_regular_file`.
    """
    top = Path(top)
    if _is_symlink_or_reparse(top):
        raise ValueError('symlinked directory or reparse point under compiler inputs: ' + str(top))
    try:
        top_info = top.lstat()
    except FileNotFoundError as error:
        if optional:
            return
        raise ValueError(f'cannot traverse compiler inputs under {top}: {error}') from error
    except OSError as error:
        raise ValueError(f'cannot traverse compiler inputs under {top}: {error}') from error
    if not stat.S_ISDIR(top_info.st_mode):
        raise ValueError('non-regular compiler input: ' + str(top))

    def traversal_error(error):
        raise ValueError(f'cannot traverse compiler inputs under {top}: {error}') from error

    for directory, names, filenames in os.walk(top, onerror=traversal_error):
        directory_path = Path(directory)
        if directory_path == top:
            names[:] = [name for name in names if name not in ('target', '.git')]
            filenames = [name for name in filenames if name not in ('target', '.git')]
        else:
            pruned_names = []
            for name in names:
                candidate = directory_path / name
                if name == '.git' and not _is_symlink_or_reparse(candidate):
                    continue
                pruned_names.append(name)
            names[:] = pruned_names
            filenames = [
                name for name in filenames
                if name != '.git' or _is_symlink_or_reparse(directory_path / name)
            ]
        for name in names:
            path = directory_path / name
            if _is_symlink_or_reparse(path):
                raise ValueError(
                    'symlinked directory or reparse point under compiler inputs: '
                    + str(path)
                )
        for name in filenames:
            path = directory_path / name
            if _is_symlink_or_reparse(path):
                raise ValueError('symlinked compiler input or reparse point: ' + str(path))
            try:
                info = path.lstat()
            except OSError as error:
                traversal_error(error)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('non-regular compiler input: ' + str(path))


def _lexical_arg(path):
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path(os.getcwd()) / candidate


def strict_manifest(crate, workspace, repository, extra_inputs=(), cwd=None):
    """Return the archived manifest after rejecting symlinked, special, or outside inputs."""
    extra_inputs = tuple(extra_inputs)
    root = Path(os.path.abspath(repository))
    resolved_root = root.resolve()
    crate_path = _plain(_lexical_arg(crate), root)
    workspace_path = _plain(_lexical_arg(workspace), root)
    cwd_path = _plain(_lexical_arg(cwd), root) if cwd is not None else resolved_root
    if not crate_path.is_relative_to(workspace_path):
        raise ValueError('crate resolves outside workspace: ' + str(crate))
    _no_linked_directories(crate_path)
    for name in ('Cargo.toml', 'Cargo.lock'):
        _check_optional_input_file(workspace_path / name)
    for directory in (crate_path, *crate_path.parents):
        _no_linked_directories(directory / 'idls', optional=True)
        if directory == workspace_path:
            break
    seen_ancestors = set()
    for start in (crate_path, cwd_path):
        for directory in (start, *start.parents):
            if directory not in seen_ancestors:
                seen_ancestors.add(directory)
                _check_optional_directory(directory / '.cargo')
                for name in ('.cargo/config', '.cargo/config.toml', 'rust-toolchain', 'rust-toolchain.toml'):
                    _check_optional_input_file(directory / name)
            if directory == resolved_root:
                break
    for extra in extra_inputs:
        extra_path = Path(extra)
        if not extra_path.is_absolute():
            cwd_candidate = Path(os.getcwd()) / extra_path
            extra_path = (
                cwd_candidate
                if cwd_candidate.exists() or _is_symlink_or_reparse(cwd_candidate)
                else root / extra_path
            )
        resolved_extra = _plain(extra_path, root)
        try:
            extra_info = resolved_extra.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISDIR(extra_info.st_mode):
            _no_linked_directories(resolved_extra)
        elif not stat.S_ISREG(extra_info.st_mode):
            raise ValueError('non-regular compiler input: ' + str(extra))
    return source_manifest(
        crate,
        workspace,
        repository,
        extra_inputs,
        cwd=cwd,
        before_read=lambda path: _plain(path, root),
    )
