"""Bounded admission for flat path-to-SHA256 research manifests."""
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat


def unique_paths(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate manifest path: ' + name)
        result[name] = value
    return result


def check_manifest(packet_dir):
    packet = Path(packet_dir)
    manifest_path = packet / 'manifest.json'
    # exists() follows links, so a dangling manifest needs its own check.
    if not manifest_path.exists() and not manifest_path.is_symlink():
        return {'status': 'no_manifest', 'errors': []}
    # The payload walk below lstats every entry under the packet root but
    # never the root itself, so a packet rooted in an external tree passed
    # admission with the external tree's own manifest and payloads. This is
    # the same gap merged #2980 closed in scripts/revalidate_all.py; the
    # retained batch revalidator (run.py) substitutes this checker, so it
    # needs the same root rejection here.
    try:
        root_metadata = packet.lstat()
    except OSError:
        root_metadata = None
    if root_metadata is not None and (
            stat.S_ISLNK(root_metadata.st_mode)
            or getattr(root_metadata, 'st_file_attributes', 0)
            & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
        return {'status': 'fail', 'files_checked': 0, 'files_expected': 0,
                'errors': ['linked_path: packet directory is a link']}
    errors, checked, expected_count = [], 0, 0
    try:
        if not stat.S_ISREG(manifest_path.lstat().st_mode) or manifest_path.is_symlink():
            raise ValueError('manifest must be a regular non-symlink file')
        raw = manifest_path.read_text(encoding='utf-8')
        # json.loads keeps only the last occurrence of a key, which would leave
        # the earlier declaration unchecked.
        manifest = json.loads(raw, object_pairs_hook=unique_paths)
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError('manifest must be a nonempty path-to-SHA256 object')
        expected_count = len(manifest)
        # Validate the complete declaration before opening any payload.
        for name, digest in manifest.items():
            path = PurePosixPath(name)
            # A colon can select an NTFS named/default stream instead of a
            # packet member, even when PureWindowsPath(name).drive is empty.
            if ':' in name:
                raise ValueError('manifest paths must not select file streams')
            if (not name or '\\' in name or path.is_absolute()
                    or PureWindowsPath(name).drive or any(part in ('', '.', '..') for part in name.split('/'))
                    or not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None):
                raise ValueError('manifest entries must be relative POSIX paths and lowercase SHA256 digests')
        for name, expected in manifest.items():
            path = packet / name
            try:
                current = packet
                for part in PurePosixPath(name).parts:
                    current = current / part
                    metadata = current.lstat()
                    if current.is_symlink() or getattr(metadata, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
                        raise ValueError('symlinked manifest payload')
                if not stat.S_ISREG(path.lstat().st_mode):
                    raise ValueError('manifest payload is not a regular file')
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                checked += 1
                if actual != expected:
                    errors.append(f'hash_mismatch: {name}')
            except (OSError, ValueError) as error:
                errors.append(f'invalid payload {name}: {type(error).__name__}')
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(f'invalid manifest: {type(error).__name__}: {error}')
    return {'status': 'fail' if errors else 'pass', 'files_checked': checked,
            'files_expected': expected_count, 'errors': errors}
