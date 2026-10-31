"""Real macOS copy/rename/lock boundaries; fixture compiler only prints sysroot.

PUMP_BUILD_TEST_SDK enables the separate genuine, pinned v1.44 compiler probe.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

import bootstrap
import test_bootstrap_macos as fixtures


@unittest.skipUnless(sys.platform == 'darwin', 'requires native macOS clone-copy and exchange')
class MacPublicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.MacHybridTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.hybrid = self.fixture.hybrid

    def old_installation(self):
        self.fixture.install_fixture()
        (self.hybrid / 'old-marker').write_bytes(b'previous installation')
        (self.hybrid / 'rust/lib/libobsolete.dylib').write_bytes(b'unused old library')

    def test_completed_replacement_retains_the_previous_tree(self):
        self.old_installation()
        self.assertTrue(bootstrap.assemble_macos())
        self.assertTrue(bootstrap.hybrid_ok())
        backups = list(self.hybrid.parent.glob('hybrid144.backup.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'old-marker').read_bytes(), b'previous installation')

    def test_interrupt_after_actual_exchange_keeps_both_trees(self):
        self.old_installation()
        rename = bootstrap.rename_toolchain

        def interrupt(source, destination, **options):
            result = rename(source, destination, **options)
            if destination == self.hybrid:
                self.assertTrue(self.hybrid.is_dir())
                raise KeyboardInterrupt('after real exchange')
            return result

        with patch.object(bootstrap, 'rename_toolchain', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            bootstrap.assemble_macos()
        self.assertTrue(bootstrap.hybrid_ok())
        retained = list(self.hybrid.parent.glob('hybrid144.stage.*/old-marker'))
        self.assertEqual(len(retained), 1, 'cleanup deleted the exchanged previous installation')
        self.assertEqual(retained[0].read_bytes(), b'previous installation')

    def test_two_assemblers_share_the_lock_and_recheck(self):
        entered, release, second_started = threading.Event(), threading.Event(), threading.Event()
        run = bootstrap.subprocess.run
        copies = []

        def pause(command, **options):
            copies.append(command)
            entered.set()
            if not release.wait(5):
                raise TimeoutError('test did not release assembly')
            return run(command, **options)

        def second():
            second_started.set()
            return bootstrap.assemble_macos()

        with patch.object(bootstrap.subprocess, 'run', side_effect=pause), ThreadPoolExecutor(2) as pool:
            first = pool.submit(bootstrap.assemble_macos)
            try:
                self.assertTrue(entered.wait(5))
                other = pool.submit(second)
                self.assertTrue(second_started.wait(5))
                self.assertFalse(other.done())
            finally:
                release.set()
            self.assertTrue(first.result(timeout=15))
            self.assertFalse(other.result(timeout=15))
        self.assertEqual(len(copies), 1)
        self.assertTrue(bootstrap.hybrid_ok())

    def test_late_directory_is_preserved_without_nesting_a_toolchain(self):
        run = bootstrap.subprocess.run

        def insert_after_staging(command, **options):
            result = run(command, **options)
            self.hybrid.mkdir()
            (self.hybrid / 'other-publisher').write_bytes(b'keep')
            return result

        with patch.object(bootstrap.subprocess, 'run', side_effect=insert_after_staging), self.assertRaises(FileExistsError):
            bootstrap.assemble_macos()
        self.assertEqual(list(self.hybrid.iterdir()), [self.hybrid / 'other-publisher'])
        self.assertEqual(list(self.hybrid.parent.glob('hybrid144.stage.*')), [])


@unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_BUILD_TEST_SDK'),
                     'set PUMP_BUILD_TEST_SDK to the authenticated macOS v1.44 SDK')
class OfficialCompilerPublicationTest(unittest.TestCase):
    def test_killed_bootstrap_keeps_a_real_pinned_compiler_at_the_canonical_path(self):
        root = Path(__file__).resolve().parents[2]
        probe = root / 'research/macos-bootstrap-publication-20261031/probe.py'
        result = subprocess.run([sys.executable, str(probe), str(root), os.environ['PUMP_BUILD_TEST_SDK']],
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertTrue(record['old_compiler_was_runnable'])
        self.assertTrue(record['canonical_exists_after_interrupt'])
        self.assertTrue(record['canonical_compiler_runnable_after_interrupt'])
        self.assertEqual(len(record['previous_files_retained_at']), 1)


if __name__ == '__main__':
    unittest.main()
