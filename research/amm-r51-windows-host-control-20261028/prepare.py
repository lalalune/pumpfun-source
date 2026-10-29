"""Prepare fresh, byte-pinned Windows r51 inputs."""
import argparse
import concurrent.futures
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def vendor_package(blob, output, record):
    """Reproduce AMM's sorted-key, LF-terminated Cargo checksum metadata.

    The sealed Mayhem helper preserves archive key order, which differs for
    these AMM inputs. Authenticate the archive and the exact generated metadata
    before writing anything; source bytes and existing pins are unchanged.
    """
    def require(ok, message):
        if not ok:
            raise ValueError(message)

    def sha(data):
        return hashlib.sha256(data).hexdigest()

    require(sha(blob) == record['package_sha256'], 'registry archive differs')
    directory = record['directory']
    require(directory not in ('', '.', '..') and PurePosixPath(directory).name == directory
            and ':' not in directory and '\\' not in directory, 'unsafe registry directory')
    contents = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as archive:
        for member in archive:
            if member.isdir():
                continue
            require(member.isfile() and member.name.startswith(directory + '/'), 'unsafe crate member')
            name = member.name[len(directory) + 1:]
            path = PurePosixPath(name)
            require(name and path.parts and not path.is_absolute() and '..' not in path.parts
                    and ':' not in name and '\\' not in name and path.as_posix() == name
                    and name != '.cargo-checksum.json' and name not in contents, 'unsafe crate path')
            contents[name] = archive.extractfile(member).read()
    require(len(contents) == record['file_count'], 'registry file count differs: ' + directory)
    checksums = {name: sha(data) for name, data in contents.items()}
    metadata = (json.dumps({'package': record['package_sha256'], 'files': checksums},
                           sort_keys=True) + '\n').encode()
    require(sha(metadata) == record['checksum_file_sha256'],
            'pinned vendor checksum map differs: ' + directory)
    target = output / directory
    target.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (target / '.cargo-checksum.json').write_bytes(metadata)


def prepare(args):
    pins = read(HERE / 'proposal-pins.json')
    dependency = args.repo.resolve() / pins['preparer_helper']['path']
    if hashlib.sha256(dependency.read_bytes()).hexdigest() != pins['preparer_helper']['sha256']:
        raise ValueError('reviewed input-preparation helper changed')
    spec = importlib.util.spec_from_file_location('pinned_input_helper', dependency)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    # Only its native inventory, authenticated acquisition, and extraction
    # functions are reused. This selects our unchanged AMM host-tool pins.
    helper.RECIPE = HERE
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        helper.native_inputs(output, args.native_inputs_sha256)
    except ValueError:
        native = output / 'native-inputs.json'
        if args.native_inputs_sha256 or not native.is_file():
            raise
        result = read(native)
        if result.get('cl_link_match_qualified_hashes') is not True:
            raise
        helper.save(output / 'prepared-inputs.json', {
            'status': 'PREFLIGHT_ONLY', 'compiler_executed': False,
            'native_manifest_sha256': result['native_manifest_sha256'],
            'next_step': 'Review this actual native byte inventory before a build dispatch.',
        })
        return
    if args.check_native_only:
        helper.save(output / 'prepared-inputs.json', {
            'status': 'NATIVE_VERIFIED', 'compiler_executed': False,
            'native_manifest_sha256': args.native_inputs_sha256,
        })
        return
    sdk = read(HERE / 'sdk-components.json.gz')
    target = read(HERE / 'linux-sysroot-inputs.json')
    archives = output / 'archives'
    windows = helper.download(pins['windows_sdk_archive']['url'],
                              archives / 'windows-v144.tar.bz2', sdk['archive_sha256'])
    linux = helper.download(target['url'], archives / 'linux-v144.tar.bz2',
                            target['archive_sha256'])
    helper.extract_components(windows, output / 'sdk', sdk['files'])
    helper.extract_components(linux, output / 'linux-sysroot', target['files'])
    acquisition = read(HERE / 'vendor-acquisition.json')
    vendor_files = read(HERE / 'vendor-files.json.gz')

    def package(record):
        name = record['name']
        archive = helper.download(record['url'], archives / (name + '.crate'), record['sha256'])
        vendor_package(archive.read_bytes(), output / 'vendor', {
            'directory': name, 'package_sha256': record['sha256'],
            'file_count': record['files'],
            'checksum_file_sha256': vendor_files[name + '/.cargo-checksum.json'],
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(package, acquisition))
    spec = importlib.util.spec_from_file_location('amm_windows_builder', HERE / 'build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.vendor_pin(output / 'vendor')
    builder.pin(output / 'sdk', {r['path']: r['sha256'] for r in sdk['files']})
    builder.pin(output / 'linux-sysroot', {r['path']: r['sha256'] for r in target['files']})
    helper.save(output / 'prepared-inputs.json', {
        'status': 'READY', 'compiler_executed': False, 'target_executions': 0,
        'sdk_archive_sha256': sdk['archive_sha256'],
        'linux_target_archive_sha256': target['archive_sha256'],
        'sdk_selected_files': len(sdk['files']), 'linux_selected_files': len(target['files']),
        'registry_packages': len(acquisition), 'vendor_files': len(vendor_files),
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-inputs-sha256', default='')
    parser.add_argument('--check-native-only', action='store_true')
    prepare(parser.parse_args())
