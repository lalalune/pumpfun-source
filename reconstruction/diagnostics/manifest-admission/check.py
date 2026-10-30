"""Bounded admission for flat path-to-SHA256 research manifests."""
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat


def check_manifest(packet_dir):
    packet = Path(packet_dir)
    manifest_path = packet / 'manifest.json'
    if not manifest_path.exists():
        return {'status': 'no_manifest', 'errors': []}
    errors, checked, expected_count = [], 0, 0
    try:
        if not stat.S_ISREG(manifest_path.lstat().st_mode) or manifest_path.is_symlink():
            raise ValueError('manifest must be a regular non-symlink file')
        raw = manifest_path.read_text(encoding='utf-8')
        manifest = json.loads(raw)
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError('manifest must be a nonempty path-to-SHA256 object')
        expected_count = len(manifest)
        # Validate the complete declaration before opening any payload.
        for name, digest in manifest.items():
            path = PurePosixPath(name)
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
