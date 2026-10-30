"""Exercise the parallel runner's output admission with actual filesystem aliases."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location(
    'parallel_input_preservation', ROOT / 'scripts/pump_validate_parallel.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ParallelInputPreservationTests(unittest.TestCase):
    def symlink(self, link, target, *, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f'symlinks are unavailable: {error}')

    def test_only_active_publications_are_selected(self):
        output = Path('packet/result.json.gz')
        suites = ('buy', 'quote_control')
        ordinary = {
            output, Path('packet/result.json.gz.failed.json'),
            Path('packet/result.json.gz.suites/buy.log'),
            Path('packet/result.json.gz.suites/buy.json.gz'),
            Path('packet/result.json.gz.suites/buy.failed-output'),
            Path('packet/result.json.gz.suites/quote_control.log'),
            Path('packet/result.json.gz.suites/quote_control.json.gz'),
            Path('packet/result.json.gz.suites/quote_control.failed-output'),
        }
        captured = ordinary | {
            Path('packet/result.json.gz.suites/buy.loader.json'),
            Path('packet/result.json.gz.suites/quote_control.loader.json'),
        }
        self.assertEqual(set(runner.report_destinations(output, suites, False, True)), ordinary)
        self.assertEqual(set(runner.report_destinations(output, suites, True, True)), captured)
        for captured_loader in (False, True):
            self.assertEqual(runner.report_destinations(output, suites, captured_loader, False), [output])

    def check_aliases(self, kind):
        # Check the aggregate, failure report, both logs, both compressed suite
        # reports, both rejected-output sidecars and both captured-loader
        # receipts without mocking filesystem APIs.
        for index in range(10):
            with self.subTest(kind=kind, destination=index), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                output = root / 'reports' / 'result.json.gz'
                destinations = runner.report_destinations(
                    output, ('buy', 'quote_control'), True, True)
                destination = destinations[index]
                destination.parent.mkdir(parents=True, exist_ok=True)
                protected = destination if kind == 'canonical' else root / 'captured-input.bin'
                original = b'preserve the bound input bytes\n'
                protected.write_bytes(original)
                if kind == 'symlink':
                    self.symlink(destination, protected)
                elif kind == 'hardlink':
                    os.link(protected, destination)
                with self.assertRaisesRegex(ValueError, 'validation output aliases a bound input'):
                    runner.protect_inputs(destinations, [protected])
                self.assertEqual(protected.read_bytes(), original)
                self.assertEqual(destination.read_bytes(), original)
                if kind == 'symlink':
                    self.assertTrue(destination.is_symlink())

    def test_every_active_destination_rejects_canonical_input(self):
        self.check_aliases('canonical')

    def test_every_active_destination_rejects_symlink_input_alias(self):
        self.check_aliases('symlink')

    def test_every_active_destination_rejects_hardlink_input_alias(self):
        self.check_aliases('hardlink')

    def test_alias_in_parent_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / 'actual'
            actual.mkdir()
            protected = actual / 'result.json.gz'
            protected.write_bytes(b'retained input')
            alias = root / 'alias'
            self.symlink(alias, actual, directory=True)
            for destination, source in ((alias / protected.name, protected),
                                        (protected, alias / protected.name)):
                with self.subTest(destination=destination), self.assertRaises(ValueError):
                    runner.protect_inputs([destination], [source])
            self.assertEqual(protected.read_bytes(), b'retained input')

    def test_unrelated_existing_output_and_inactive_sidecars_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'result.json.gz'
            output.write_bytes(b'previous report')
            protected = root / 'captured-input.bin'
            protected.write_bytes(b'bound input')
            failure = root / 'result.json.gz.failed.json'
            os.link(protected, failure)
            # Revalidation only writes the aggregate, so a retained execution
            # failure sidecar does not create a false conflict in this mode.
            destinations = runner.report_destinations(output, ('buy',), True, False)
            runner.protect_inputs(destinations, [protected])
            self.assertEqual(output.read_bytes(), b'previous report')
            self.assertEqual(protected.read_bytes(), b'bound input')


if __name__ == '__main__':
    unittest.main()
