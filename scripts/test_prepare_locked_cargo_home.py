"""Exercise cache preparation against an isolated Cargo home without network access."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


class CargoHomeTests(unittest.TestCase):
    def prepare_with_changed_source(self, kind, phase):
        # The retained real crate/index bytes are copied normally. The hook only
        # schedules an actual filesystem change at an otherwise timing-dependent
        # boundary; it does not fake a read, copy, checksum, or CLI result.
        fixture = Path(__file__).with_name('fixtures') / 'cargo-index-case'
        archive_bytes = (fixture / 'Inflector-0.11.4.crate').read_bytes()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        rows = [json.loads(line) for line in (fixture / 'inflector-index.jsonl').read_bytes().splitlines()]
        index_bytes = self.sparse_cache(*rows)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'home'
            namespace = 'index.crates.io-1949cf8c6b5b557f'
            paths = {
                'archive': home / 'registry/cache' / namespace / 'Inflector-0.11.4.crate',
                'index': home / 'registry/index' / namespace / '.cache/in/fl/inflector',
                'config': home / 'registry/index' / namespace / 'config.json',
            }
            for name, data in [('archive', archive_bytes), ('index', index_bytes),
                               ('config', b'{"dl":"https://static.crates.io/crates"}')]:
                paths[name].parent.mkdir(parents=True, exist_ok=True)
                paths[name].write_bytes(data)
            lock = root / 'Cargo.lock'
            lock.write_text('version = 3\n[[package]]\nname="Inflector"\nversion="0.11.4"\n'
                            'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')
            injections = root / 'injections'
            injections.mkdir()
            (injections / 'sitecustomize.py').write_text('''import os
from pathlib import Path
import shutil
source = Path(os.environ['CHANGED_CACHE_SOURCE'])
phase = os.environ['CHANGE_CACHE_PHASE']
read_bytes = Path.read_bytes
copyfile = shutil.copyfile
count = 0
def change():
    source.write_bytes(b'changed while preparing the cache')
    Path(os.environ['CHANGE_CACHE_MARKER']).write_text('changed')
def read(path):
    data = read_bytes(path)
    if path == source and phase == 'after_read':
        change()
    return data
def copy(origin, destination, *args, **kwargs):
    global count
    if Path(origin) == source:
        count += 1
        if phase == 'copy_' + str(count):
            change()
    return copyfile(origin, destination, *args, **kwargs)
Path.read_bytes = read
shutil.copyfile = copy
''', encoding='utf-8')
            output = root / 'output'
            marker = root / 'changed'
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                 '--lockfile', str(lock), '--output', str(output)],
                env={**os.environ, 'CARGO_HOME': str(home), 'PYTHONPATH': str(injections),
                     'CHANGED_CACHE_SOURCE': str(paths[kind]), 'CHANGE_CACHE_PHASE': phase,
                     'CHANGE_CACHE_MARKER': str(marker)}, capture_output=True, text=True)
            self.assertTrue(marker.is_file(), 'the source-change boundary was not exercised')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('changed while preparing', result.stderr)
            self.assertFalse(output.exists(), 'published cache contains unverified bytes')
            self.assertEqual(list(root.glob('.output.*')), [])

    def test_changed_sources_are_rejected_in_either_namespace_copy(self):
        for kind in ('archive', 'index', 'config'):
            for phase in ('copy_1', 'copy_2'):
                with self.subTest(kind=kind, phase=phase):
                    self.prepare_with_changed_source(kind, phase)

    def test_index_hash_binds_the_bytes_used_for_locked_record_admission(self):
        self.prepare_with_changed_source('index', 'after_read')

    def run_empty_cache(self, root, output, extra_env=None):
        lock = root / 'empty.lock'
        lock.write_text('version = 3\npackage = []\n', encoding='utf-8')
        command = [sys.executable, '-c',
                   "import os,runpy,sys; os.umask(0o027); "
                   "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')",
                   str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                   '--lockfile', str(lock), '--output', str(output)]
        return subprocess.run(command, env={**os.environ, **(extra_env or {})},
                              capture_output=True, text=True)

    def test_existing_empty_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output'
            output.mkdir()
            result = self.run_empty_cache(root, output)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(root.glob('.output.*')), [])

    def test_late_empty_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output'
            injections = root / 'injections'
            injections.mkdir()
            (injections / 'sitecustomize.py').write_text(
                'import os\nfrom pathlib import Path\n'
                'real_write = Path.write_text\n'
                'def write(self, *args, **kwargs):\n'
                '    result = real_write(self, *args, **kwargs)\n'
                "    if self.name == 'cache-manifest.json':\n"
                "        Path(os.environ['LATE_OUTPUT']).mkdir()\n"
                '    return result\n'
                'Path.write_text = write\n', encoding='utf-8')
            result = self.run_empty_cache(root, output,
                {'PYTHONPATH': str(injections), 'LATE_OUTPUT': str(output)})
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(root.glob('.output.*')), [])

    @unittest.skipIf(os.name == 'nt', 'Windows uses its native no-replace rename')
    def test_unavailable_atomic_publication_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output'
            injections = root / 'injections'
            injections.mkdir()
            (injections / 'sitecustomize.py').write_text(
                'import ctypes\nctypes.CDLL = lambda *args, **kwargs: object()\n', encoding='utf-8')
            result = self.run_empty_cache(root, output, {'PYTHONPATH': str(injections)})
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('atomic no-replace directory publication unavailable', result.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob('.output.*')), [])

    @unittest.skipUnless(os.name == 'posix', 'POSIX permission mode check')
    def test_published_directory_keeps_the_process_umask(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output'
            result = self.run_empty_cache(root, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.stat().st_mode & 0o777, 0o750)
            self.assertTrue((output / 'cache-manifest.json').is_file())
            self.assertEqual(list(root.glob('.output.*')), [])

    @staticmethod
    def sparse_cache(*records):
        return b'\x03\x02\x00\x00\x00offline-fixture\x00' + b''.join(
            record['vers'].encode() + b'\0' + json.dumps(record, separators=(',', ':')).encode() + b'\0'
            for record in records
        )

    def test_shared_index_covers_every_locked_version_in_either_lock_order(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                self.prepare_multiple_versions(reverse=reverse)

    def test_disjoint_indexes_are_rejected_before_creating_output(self):
        self.prepare_multiple_versions(disjoint=True)

    def prepare_multiple_versions(self, reverse=False, disjoint=False):
        # Synthetic metadata/cache controls; no Cargo or program executes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'home'
            namespaces = ('index.crates.io-1949cf8c6b5b557f',
                          'index.crates.io-6f17d22bba15001f')
            versions = ('1.0.0', '2.0.0')
            records = [{'name': 'cache-probe', 'vers': version,
                        'cksum': hashlib.sha256(version.encode()).hexdigest()}
                       for version in versions]
            for position, namespace in enumerate(namespaces):
                directory = home / 'registry/index' / namespace
                (directory / '.cache/ca/ch').mkdir(parents=True)
                available = [records[1]] if position == 0 else records[:1] if disjoint else records
                (directory / '.cache/ca/ch/cache-probe').write_bytes(self.sparse_cache(*available))
                (directory / 'config.json').write_text('{}')
            cache = home / 'registry/cache' / namespaces[0]
            cache.mkdir(parents=True)
            for version in versions:
                (cache / f'cache-probe-{version}.crate').write_bytes(version.encode())
            lock = root / 'Cargo.lock'
            lock.write_text('version = 3\n' + ''.join(
                '[[package]]\nname="cache-probe"\n'
                f'version="{record["vers"]}"\n'
                'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                f'checksum="{record["cksum"]}"\n'
                for record in (list(reversed(records)) if reverse else records)))
            output = root / 'output'
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                 '--lockfile', str(lock), '--output', str(output)],
                env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            if disjoint:
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_bytes())
            expected = self.sparse_cache(*records)
            for namespace in namespaces:
                actual = (output / 'registry/index' / namespace / '.cache/ca/ch/cache-probe').read_bytes()
                self.assertEqual(actual, expected)
                for package in manifest['packages']:
                    self.assertEqual(package['index_sha256'], hashlib.sha256(actual).hexdigest())

    def test_stale_preferred_index_uses_checksum_matching_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            stale_namespace = 'index.crates.io-1949cf8c6b5b557f'
            valid_namespace = 'index.crates.io-6f17d22bba15001f'
            archive_bytes = b'checksum-matched archive'
            digest = hashlib.sha256(archive_bytes).hexdigest()
            relative = Path('ca/ch/cache-probe')
            for namespace in (stale_namespace, valid_namespace):
                archive = home / 'registry/cache' / namespace / 'cache-probe-1.0.0.crate'
                archive.parent.mkdir(parents=True)
                archive.write_bytes(archive_bytes)
            stale_index = self.sparse_cache(
                {'name': 'cache-probe', 'vers': '1.0.0', 'cksum': '0' * 64})
            valid_index = self.sparse_cache(
                {'name': 'cache-probe', 'vers': '1.0.0', 'cksum': digest})
            for namespace, index_bytes in ((stale_namespace, stale_index),
                                           (valid_namespace, valid_index)):
                index = home / 'registry/index' / namespace / '.cache' / relative
                index.parent.mkdir(parents=True)
                index.write_bytes(index_bytes)
                (index.parents[3] / 'config.json').write_text('{}', encoding='utf-8')
            lock = root / 'Cargo.lock'
            lock.write_text('[[package]]\nname="cache-probe"\nversion="1.0.0"\n'
                            'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_text())
            self.assertEqual(manifest['packages'][0]['index_sha256'],
                             hashlib.sha256(valid_index).hexdigest())
            for namespace in (stale_namespace, valid_namespace):
                target = output / 'registry/index' / namespace / '.cache' / relative
                self.assertEqual(target.read_bytes(), valid_index)

    def test_no_checksum_matching_index_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            namespace = 'index.crates.io-1949cf8c6b5b557f'
            archive = home / 'registry/cache' / namespace / 'cache-probe-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'checksum-matched archive')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            index = home / 'registry/index' / namespace / '.cache/ca/ch/cache-probe'
            index.parent.mkdir(parents=True)
            index.write_bytes(self.sparse_cache(
                {'name': 'cache-probe', 'vers': '1.0.0', 'cksum': '0' * 64}))
            (index.parents[3] / 'config.json').write_text('{}', encoding='utf-8')
            lock = root / 'Cargo.lock'
            lock.write_text('[[package]]\nname="cache-probe"\nversion="1.0.0"\n'
                            'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(root / 'output')],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('No checksum-matching sparse-index record', result.stderr)

    def test_failed_copy_does_not_leave_a_partial_cache_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            namespace = 'index.crates.io-1949cf8c6b5b557f'
            archive = home / 'registry/cache' / namespace / 'cache-probe-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'checksum-matched archive')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            index = home / 'registry/index' / namespace / '.cache/ca/ch/cache-probe'
            index.parent.mkdir(parents=True)
            index.write_bytes(self.sparse_cache(
                {'name': 'cache-probe', 'vers': '1.0.0', 'cksum': digest}))
            (index.parents[3] / 'config.json').write_text('{}', encoding='utf-8')
            lock = root / 'Cargo.lock'
            lock.write_text('[[package]]\nname="cache-probe"\nversion="1.0.0"\n'
                            'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')

            injections = root / 'injections'
            injections.mkdir()
            (injections / 'sitecustomize.py').write_text(
                'import shutil\n'
                'real_copyfile = shutil.copyfile\n'
                'copy_count = 0\n'
                'def interrupted_copyfile(*args, **kwargs):\n'
                '    global copy_count\n'
                '    copy_count += 1\n'
                '    if copy_count == 2:\n'
                "        raise OSError('injected cache copy failure')\n"
                '    return real_copyfile(*args, **kwargs)\n'
                'shutil.copyfile = interrupted_copyfile\n',
                encoding='utf-8',
            )
            output = root / 'output'
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                 '--lockfile', str(lock), '--output', str(output)],
                env={**os.environ, 'CARGO_HOME': str(home),
                     'PYTHONPATH': str(injections)},
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('injected cache copy failure', result.stderr)
            self.assertFalse(output.exists(), 'failed preparation left a partial cache output')
            self.assertEqual(list(root.glob('.output.*')), [])

    def test_matching_index_is_consumable_by_offline_cargo(self):
        cargo = shutil.which('cargo')
        if cargo is None:
            self.skipTest('cargo is not installed')
        name, version = 'cache-probe', '1.0.0'
        archive_buffer = io.BytesIO()
        with tarfile.open(fileobj=archive_buffer, mode='w:gz') as archive_file:
            for relative, data in (
                ('Cargo.toml', f'[package]\nname = "{name}"\nversion = "{version}"\nedition = "2021"\n'),
                ('src/lib.rs', 'pub fn probe() {}\n'),
            ):
                payload = data.encode()
                info = tarfile.TarInfo(f'{name}-{version}/{relative}')
                info.size = len(payload)
                archive_file.addfile(info, io.BytesIO(payload))
        archive_bytes = archive_buffer.getvalue()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        cache_bytes = self.sparse_cache({
            'name': name, 'vers': version, 'deps': [], 'cksum': digest,
            'features': {}, 'yanked': False, 'links': None,
        })
        namespace = 'index.crates.io-1949cf8c6b5b557f'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            archive = home / 'registry/cache' / namespace / f'{name}-{version}.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(archive_bytes)
            index = home / 'registry/index' / namespace / '.cache/ca/ch/cache-probe'
            index.parent.mkdir(parents=True)
            index.write_bytes(cache_bytes)
            (index.parents[3] / 'config.json').write_text(
                '{"dl":"https://static.crates.io/crates","api":"https://crates.io"}', encoding='utf-8')
            lock_text = (f'version = 3\n[[package]]\nname="{name}"\nversion="{version}"\n'
                         'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                         f'checksum="{digest}"\n')
            lock = root / 'Cargo.lock'
            lock.write_text(lock_text, encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            project = root / 'project'
            (project / 'src').mkdir(parents=True)
            (project / 'src/lib.rs').write_text('pub fn probe() {}\n', encoding='utf-8')
            (project / 'Cargo.toml').write_text(
                '[package]\nname = "offline-index-probe"\nversion = "0.1.0"\nedition = "2021"\n\n'
                f'[dependencies]\n{name} = "={version}"\n', encoding='utf-8')
            (project / 'Cargo.lock').write_text(lock_text, encoding='utf-8')
            cargo_result = subprocess.run(
                [cargo, 'metadata', '--offline', '--format-version', '1',
                 '--manifest-path', str(project / 'Cargo.toml')],
                env={**os.environ, 'CARGO_HOME': str(output), 'CARGO_NET_OFFLINE': 'true'},
                capture_output=True, text=True)
            self.assertEqual(cargo_result.returncode, 0, cargo_result.stderr)

    def test_real_mixed_case_package_uses_lowercase_index_path(self):
        fixture = Path(__file__).with_name('fixtures') / 'cargo-index-case'
        archive_bytes = (fixture / 'Inflector-0.11.4.crate').read_bytes()
        index_bytes = (fixture / 'inflector-index.jsonl').read_bytes()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        self.assertEqual(digest, 'fe438c63458706e03479442743baae6c88256498e6431708f6dfc520a26515d3')
        self.assertEqual(hashlib.sha256(index_bytes).hexdigest(), 'cb2b8f9cd2baa2934fa604108cd792b30f83b4ba32de329607046984d2213957')
        rows = [(json.loads(line), line) for line in index_bytes.splitlines()]
        selected = [record for record, _ in rows if record['vers'] == '0.11.4']
        self.assertEqual(len(selected), 1)
        self.assertEqual((selected[0]['name'], selected[0]['cksum']), ('Inflector', digest))
        cache_bytes = b'\x03\x02\x00\x00\x00offline-fixture\x00' + b''.join(
            record['vers'].encode('utf-8') + b'\x00' + raw + b'\x00' for record, raw in rows)
        namespaces = ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f')
        for namespace in namespaces:
            with self.subTest(namespace=namespace), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                home = root / 'home'
                archive = home / 'registry/cache' / namespace / 'Inflector-0.11.4.crate'
                archive.parent.mkdir(parents=True)
                archive.write_bytes(archive_bytes)
                index = home / 'registry/index' / namespace / '.cache/in/fl/inflector'
                index.parent.mkdir(parents=True)
                index.write_bytes(cache_bytes)
                (home / 'registry/index' / namespace / 'config.json').write_text(
                    '{"dl":"https://static.crates.io/crates","api":"https://crates.io"}', encoding='utf-8')
                lock = root / 'Cargo.lock'
                lock.write_text('version = 3\n[[package]]\nname="Inflector"\nversion="0.11.4"\n'
                                'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                                f'checksum="{digest}"\n', encoding='utf-8')
                output = root / 'output'
                result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                         '--lockfile', str(lock), '--output', str(output)],
                                        env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                paths = {path.relative_to(output).as_posix() for path in output.rglob('*') if path.is_file()}
                for target in namespaces:
                    canonical = f'registry/index/{target}/.cache/in/fl/inflector'
                    self.assertIn(canonical, paths)  # Also detects spelling errors on case-insensitive hosts.
                    self.assertEqual((output / canonical).read_bytes(), cache_bytes)
                    self.assertEqual((output / 'registry/cache' / target / archive.name).read_bytes(), archive_bytes)

    def test_path_only_lockfile_needs_no_registry_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / 'Cargo.lock'
            lock.write_text('version = 3\n[[package]]\nname = "local-only"\nversion = "1.0.0"\n', encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(root / 'absent-cargo-home')}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_text())
            self.assertEqual(manifest['packages'], [])
            self.assertIsNone(manifest['registry_config_sha256'])
            self.assertEqual(manifest['lockfile_sha256'], hashlib.sha256(lock.read_bytes()).hexdigest())
            self.assertTrue((output / 'registry').is_dir())
            self.assertEqual(list((output / 'registry').iterdir()), [])
            self.assertFalse((root / 'absent-cargo-home').exists())

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_SUPPORTED_TEST_TOOLS'),
                         'requires authenticated v1.53 SDK and pinned v1.52 objcopy')
    def test_supported_build_accepts_prepared_local_only_caches(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='empty-cache-sdk-test-') as temporary:
            output = Path(temporary) / 'result.json'
            result = subprocess.run([sys.executable, '-B',
                str(repo / 'research/empty-registry-cache-20261101/probe.py'), '--repo', str(repo),
                '--tools', os.environ['PUMP_SUPPORTED_TEST_TOOLS'], '--expect', 'fixed', '--output', str(output)],
                capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(output.read_text())
            self.assertEqual(set(record['build_cases']), {'dependency_free', 'local_path_only'})

    def test_supported_cache_namespaces_supply_configuration(self):
        for namespace in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
            with self.subTest(namespace=namespace):
                self.prepare_from_namespace(namespace)

    def test_mixed_case_package_indexes_use_lowercase_paths(self):
        # Cargo's index files use lowercase names and directory prefixes:
        # https://doc.rust-lang.org/cargo/reference/registry-index.html#index-files
        cases = [('A', '1/a'), ('Ab', '2/ab'), ('AbC', '3/a/abc'),
                 ('AbCd', 'ab/cd/abcd'), ('MixedCase', 'mi/xe/mixedcase')]
        for namespace in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
            for name, relative in cases:
                with self.subTest(namespace=namespace, name=name):
                    self.prepare_from_namespace(namespace, name, relative)

    def test_alternative_registry_is_rejected_before_output_creation(self):
        self.prepare_from_namespace(
            'index.crates.io-1949cf8c6b5b557f',
            registry_source='registry+https://registry.example.invalid/index',
            rejected=True,
        )

    def prepare_from_namespace(self, namespace, name='cache-probe', relative='ca/ch/cache-probe',
                               registry_source='registry+https://github.com/rust-lang/crates.io-index',
                               rejected=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            archive = home / 'registry/cache' / namespace / f'{name}-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'isolated archive')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            index = home / 'registry/index' / namespace / '.cache' / relative
            index.parent.mkdir(parents=True)
            index.write_bytes(self.sparse_cache(
                {'name': name, 'vers': '1.0.0', 'cksum': digest}))
            config = home / 'registry/index' / namespace / 'config.json'
            config.write_text('{}', encoding='utf-8')
            lock = root / 'Cargo.lock'
            lock.write_text(f'[[package]]\nname="{name}"\nversion="1.0.0"\n'
                            f'source="{registry_source}"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            if rejected:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Unsupported registry source', result.stderr)
                self.assertFalse(output.exists())
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_text())
            self.assertEqual(manifest['packages'][0]['package'], name)
            self.assertEqual(manifest['packages'][0]['archive_sha256'], digest)
            for target in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
                self.assertEqual((output / 'registry/cache' / target / archive.name).read_bytes(), archive.read_bytes())
                self.assertEqual((output / 'registry/index' / target / '.cache' / relative).read_bytes(), index.read_bytes())
                # Inspect stored spellings: exists/read_bytes can hide a wrong
                # case on case-insensitive filesystems.
                stored = {path.relative_to(output).as_posix() for path in output.rglob('*') if path.is_file()}
                self.assertIn(f'registry/index/{target}/.cache/{relative}', stored)
                self.assertIn(f'registry/cache/{target}/{name}-1.0.0.crate', stored)


if __name__ == '__main__':
    unittest.main()
