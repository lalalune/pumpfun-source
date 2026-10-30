#!/usr/bin/env python3
"""Prepare an isolated offline crates.io cache from checksum-verified local archives."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
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
for package in lock['package']:
    registry_source = package.get('source', '')
    if (registry_source.startswith('registry+') and
            registry_source != 'registry+https://github.com/rust-lang/crates.io-index'):
        parser.error('Unsupported registry source; this helper only prepares crates.io packages')
args.output.mkdir(parents=True, exist_ok=False)
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

records = []
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
    indexes = sorted((source / 'index').glob('*/.cache/' + relative),
                     key=lambda path: '1949cf8' not in str(path))
    if not indexes:
        raise RuntimeError(f'No local sparse-index metadata: {name}')
    for namespace in namespaces:
        archive_target = args.output / 'registry/cache' / namespace / filename
        index_target = args.output / 'registry/index' / namespace / '.cache' / relative
        archive_target.parent.mkdir(parents=True, exist_ok=True)
        index_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archives[0], archive_target)
        shutil.copyfile(indexes[0], index_target)
    records.append({'package': name, 'version': version,
                    'archive_sha256': package['checksum'],
                    'index_sha256': sha(indexes[0])})
config = None
if records:
    configs = [source / 'index' / namespace / 'config.json'
               for namespace in reversed(namespaces)
               if (source / 'index' / namespace / 'config.json').is_file()]
    if not configs:
        raise RuntimeError('No local crates.io registry configuration')
    config = configs[0]
    for namespace in namespaces:
        shutil.copyfile(config, args.output / 'registry/index' / namespace / 'config.json')
manifest = {'scope': 'Existing local archives verified against a fixed Cargo.lock; no network download.',
            'lockfile_sha256': hashlib.sha256(raw_lock).hexdigest(),
            'registry_config_sha256': sha(config) if config is not None else None, 'packages': records}
(args.output / 'cache-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Prepared {len(records)} checksum-verified packages in {args.output}')
