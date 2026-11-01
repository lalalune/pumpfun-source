"""Admission controls for the v3 buy-crossing applied data-section comparison."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

LANE = Path(__file__).resolve().parents[1] / 'reconstruction/pump-main/lanes/v3-buy-crossing-layout'


def load():
    spec = importlib.util.spec_from_file_location('v3_buy_crossing_packet', LANE / 'verify_packet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SectionComparisonTests(unittest.TestCase):
    def setUp(self):
        self.verify = load()

    def audit(self, sections):
        return {'sections_equal': sections}

    def test_both_sections_equal_is_accepted(self):
        self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': True}))

    def test_changed_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data sections changed'):
            self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': False}))

    def test_truthy_non_boolean_comparison_is_rejected(self):
        for value in (1, 'true', ['equal'], {'.text': True}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'applied data sections changed'):
                self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': value}))

    def test_section_name_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit(['.rodata', '.data.rel.ro']))

    def test_empty_comparison_is_rejected(self):
        # all({}.values()) is True, so an emptied audit used to pass the check.
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit({}))

    def test_dropped_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit({'.rodata': True}))

    def test_unexpected_section_is_rejected(self):
        sections = {'.rodata': True, '.data.rel.ro': True, '.text': True}
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit(sections))


class PacketMembershipTests(unittest.TestCase):
    def command(self, packet, *args):
        return subprocess.run([sys.executable, '-B', str(packet / 'verify_packet.py'), *args],
                              capture_output=True, text=True, timeout=60)

    def test_pristine_retained_scores_and_signatures_pass(self):
        result = self.command(LANE, '--signatures')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['receipts'], 612)
        self.assertTrue(json.loads(result.stdout)['signatures_checked'])

    def test_unlisted_reserved_names_and_cached_bytecode_are_rejected(self):
        for extra in ('nested/manifest.json', '__pycache__/unlisted.txt', '__pycache__/reader.pyc'):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temporary:
                packet = Path(temporary) / 'packet'
                shutil.copytree(LANE, packet)
                path = packet / extra
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'{}')
                result = self.command(packet)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('cached bytecode' if extra.endswith('.pyc') else 'file set differs',
                              result.stderr)

    def test_duplicate_manifest_path_is_rejected_even_with_the_same_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / 'packet'
            shutil.copytree(LANE, packet)
            manifest = packet / 'manifest.json'
            raw = manifest.read_text()
            rows = json.loads(raw)
            repeated = json.dumps('NOTES.md') + ':' + json.dumps(rows['NOTES.md']) + ','
            manifest.write_text('{' + repeated + raw.lstrip()[1:])
            result = self.command(packet)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('duplicate packet manifest path', result.stderr)


if __name__ == '__main__':
    unittest.main()
