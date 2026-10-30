"""Linux hybrid admission, recovery and cross-process publication boundaries."""
import fcntl
import multiprocessing
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reconstruction/toolchain'))
import bootstrap
import test_bootstrap_linux as fixtures


class LinuxHybridPublication(fixtures.LinuxToolchainTests):
    def test_host_shared_libraries_are_verified_against_the_sdk(self):
        bootstrap.assemble_linux()
        library = self.hybrid / 'rust/lib/libstd-example.so'
        for changed in [None, b'changed host library']:
            with self.subTest(changed=changed):
                if changed is None:
                    library.unlink()
                else:
                    library.write_bytes(changed)
                self.assertFalse(bootstrap.hybrid_ok_linux())
                bootstrap.assemble_linux()
                self.assertTrue(bootstrap.hybrid_ok_linux())
        (self.hybrid / 'rust/lib/libunexpected.so').write_bytes(b'unlisted')
        self.assertFalse(bootstrap.hybrid_ok_linux())

    def test_failed_publication_restores_previous_canonical_toolchain(self):
        bootstrap.assemble_linux()
        marker = self.hybrid / 'old-installation'
        marker.write_bytes(b'working installation')
        # Make replacement necessary without touching the admitted SDK.
        (self.hybrid / 'rust/bin/rustc').write_bytes(b'old compiler')
        rename = Path.rename
        def fail_stage(path, destination):
            if path.name.startswith(self.hybrid.name + '.stage.'):
                raise OSError('injected stage publication failure')
            return rename(path, destination)
        with patch.object(Path, 'rename', fail_stage), self.assertRaisesRegex(OSError, 'publication failure'):
            bootstrap.assemble_linux()
        self.assertEqual(marker.read_bytes(), b'working installation')
        self.assertEqual(list(self.hybrid.parent.glob('*.stage.*')), [])
        self.assertEqual(list(self.hybrid.parent.glob('*.backup.*')), [])
        bootstrap.assemble_linux()
        self.assertTrue(bootstrap.hybrid_ok_linux())

    def test_two_assemblers_share_a_lock_and_recheck_before_copying(self):
        self.hybrid.parent.mkdir(parents=True)
        context = multiprocessing.get_context('fork')
        started = [context.Event(), context.Event()]
        copied = context.Event()
        copies = context.Value('i', 0)
        errors = context.Queue()
        copy = bootstrap.shutil.copy2
        def worker(index):
            def observe(source, destination, *args, **kwargs):
                if Path(source) == self.rustc:
                    with copies.get_lock():
                        copies.value += 1
                    copied.set()
                return copy(source, destination, *args, **kwargs)
            try:
                with patch.object(bootstrap.shutil, 'copy2', observe):
                    started[index].set()
                    bootstrap.assemble_linux()
                errors.put(None)
            except BaseException as error:
                errors.put(repr(error))
        processes = [context.Process(target=worker, args=(index,)) for index in range(2)]
        with (self.hybrid.parent / (self.hybrid.name + '.lock')).open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                for process in processes:
                    process.start()
                for event in started:
                    self.assertTrue(event.wait(5))
                blocked = not copied.wait(0.2)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
                for process in processes:
                    process.join(10)
                    if process.is_alive():
                        process.kill()
                        process.join()
            self.assertTrue(blocked, 'assembly ignored the shared publication lock')
        self.assertEqual([errors.get(timeout=2) for _ in processes], [None, None])
        self.assertEqual(copies.value, 1, 'second publisher did not reuse the intact installation')
        self.assertTrue(bootstrap.hybrid_ok_linux())
        self.assertEqual(list(self.hybrid.parent.glob('*.stage.*')), [])
        self.assertEqual(list(self.hybrid.parent.glob('*.backup.*')), [])


if __name__ == '__main__':
    unittest.main()
