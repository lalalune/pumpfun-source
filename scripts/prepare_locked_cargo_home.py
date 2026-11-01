#!/usr/bin/env python3
"""Prepare an isolated offline crates.io cache from checksum-verified local archives."""
import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import sys
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--lockfile', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = Path(os.environ.get('CARGO_HOME') or Path.home() / '.cargo').expanduser() / 'registry'
args.output = args.output.resolve()
raw_lock = args.lockfile.read_bytes()
lock = tomllib.loads(raw_lock.decode())
# Output namespaces and registry configuration below are specific to crates.io.
# Reject other registries before creating a partial or mislabeled cache.
registry_packages = {}
for package in lock['package']:
    registry_source = package.get('source', '')
    if (registry_source.startswith('registry+') and
            registry_source != 'registry+https://github.com/rust-lang/crates.io-index'):
        parser.error('Unsupported registry source; this helper only prepares crates.io packages')
    if registry_source.startswith('registry+'):
        registry_packages.setdefault(package['name'], []).append(package)
namespaces = ['index.crates.io-6f17d22bba15001f', 'index.crates.io-1949cf8c6b5b557f']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def index_path(name):
    # Cargo lowercases index paths, while archive names retain package casing.
    name = name.lower()
    if len(name) == 1:
        return '1/' + name
    if len(name) == 2:
        return '2/' + name
    if len(name) == 3:
        return '3/' + name[0] + '/' + name
    return name[:2] + '/' + name[2:4] + '/' + name

def index_records(raw_index):
    # Cargo stores sparse-index records as JSON segments in a NUL-delimited cache envelope.
    for raw in raw_index.split(b'\0'):
        if not raw.startswith(b'{'):
            continue
        try:
            record = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            yield record


def supplies_locked_versions(raw_index, name):
    records = list(index_records(raw_index))
    # Every version of a crate shares one output index pathname. Selecting
    # per-version inputs can overwrite an earlier package's admitted metadata.
    return all(any(record.get('name') == name and record.get('vers') == package['version']
                   and record.get('cksum') == package['checksum'] for record in records)
               for package in registry_packages[name])

records, copies = [], []
selected_indexes = {}
for package in lock['package']:
    if not package.get('source', '').startswith('registry+'):
        continue
    name, version = package['name'], package['version']
    filename = f'{name}-{version}.crate'
    archives = [path for path in (source / 'cache').glob('*/' + filename)
                if sha(path) == package['checksum']]
    if not archives:
        raise RuntimeError(f'No checksum-verified cached archive: {filename}')
    relative = index_path(name)
    if name not in selected_indexes:
        indexes = sorted((source / 'index').glob('*/.cache/' + relative),
                         key=lambda path: '1949cf8' not in str(path))
        if not indexes:
            raise RuntimeError(f'No local sparse-index metadata: {name}')
        for index in indexes:
            raw_index = index.read_bytes()
            if supplies_locked_versions(raw_index, name):
                # Bind the hash to the bytes admitted above, and reuse that
                # choice for every locked version sharing this index path.
                selected_indexes[name] = (index, hashlib.sha256(raw_index).hexdigest())
                break
        else:
            raise RuntimeError(f'No checksum-matching sparse-index record for all locked versions: {name}')
    index, index_sha256 = selected_indexes[name]
    copies.append((archives[0], Path('registry/cache'), filename, package['checksum']))
    copies.append((index, Path('registry/index'), Path('.cache') / relative, index_sha256))
    records.append({'package': name, 'version': version,
                    'archive_sha256': package['checksum'],
                    'index_sha256': index_sha256})
config_sha256 = None
if records:
    configs = [source / 'index' / namespace / 'config.json'
               for namespace in reversed(namespaces)
               if (source / 'index' / namespace / 'config.json').is_file()]
    if not configs:
        raise RuntimeError('No local crates.io registry configuration')
    config = configs[0]
    config_sha256 = sha(config)
    copies.append((config, Path('registry/index'), 'config.json', config_sha256))
def publish_directory(staged, destination):
    """Atomically publish only to an absent path, including concurrent writers."""
    if os.name == 'nt':
        staged.rename(destination)  # Windows rename refuses an existing destination.
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        rename = getattr(library, 'renamex_np', None)
        arguments = (os.fsencode(staged), os.fsencode(destination), 0x00000004)
        types = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]  # RENAME_EXCL
    elif sys.platform.startswith('linux'):
        rename = getattr(library, 'renameat2', None)
        arguments = (-100, os.fsencode(staged), -100, os.fsencode(destination), 1)
        types = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                 ctypes.c_uint]  # AT_FDCWD, RENAME_NOREPLACE
    else:
        rename = None
    if rename is None:
        raise OSError(errno.ENOTSUP, 'atomic no-replace directory publication unavailable')
    rename.argtypes = types
    rename.restype = ctypes.c_int
    if rename(*arguments) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


# Every locked package resolved. Build the complete cache beside the requested
# path, then publish it with one rename; a failed copy must not poison a rerun.
args.output.parent.mkdir(parents=True, exist_ok=True)
# A valid output basename can sit at the filesystem's component limit; only
# the published name has to fit there, so keep the staging prefix short.
wrapper = Path(tempfile.mkdtemp(prefix='.' + args.output.name[:32] + '.', dir=args.output.parent))
staging = wrapper / 'cache'
try:
    staging.mkdir()  # The published directory retains ordinary umask permissions.
    # Local-only lockfiles still need the registry root expected by build adapters.
    (staging / 'registry').mkdir()
    for origin, area, name, expected in copies:
        for namespace in namespaces:
            target = staging / area / namespace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, target)
            # Source caches may change after admission or between namespace
            # copies. Only publish the bytes whose digests were admitted.
            if sha(target) != expected:
                raise RuntimeError(f'Cached input changed while preparing: {origin}')
    manifest = {'scope': 'Existing local archives verified against a fixed Cargo.lock; no network download.',
                'lockfile_sha256': hashlib.sha256(raw_lock).hexdigest(),
                'registry_config_sha256': config_sha256, 'packages': records}
    (staging / 'cache-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',encoding='utf-8',newline='\n')
    publish_directory(staging, args.output)
finally:
    shutil.rmtree(wrapper, ignore_errors=True)
print(f'Prepared {len(records)} checksum-verified packages in {args.output}')
