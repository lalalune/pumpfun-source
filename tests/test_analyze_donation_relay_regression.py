"""Offline coverage of the retained Donation Relay capture, without executing it."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze as analysis


class DonationRelayTests(unittest.TestCase):
    def test_real_donation_capture_is_selected_and_analyzed(self):
        raw = (ROOT / 'evidence/dependencies/donation_relay/deployed.so').read_bytes()
        expected = analysis.elf_layout(raw)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / 'evidence/dependencies/donation_relay',
                            root / 'evidence/dependencies/donation_relay')
            # analyze refuses to publish an empty interface inventory, so
            # supply one real upstream IDL alongside the relay capture.
            (root / 'evidence/upstream').mkdir(parents=True)
            shutil.copyfile(ROOT / 'evidence/upstream/pump.json',
                            root / 'evidence/upstream/pump.json')
            with patch.object(analysis, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(analysis.program_names(), ['donation_relay'])
                capture = json.loads((root / 'evidence/dependencies/donation_relay/capture.json').read_text())
                self.assertEqual(analysis.program_addresses(), {'donation_relay': capture['program']})
                analysis.analyze()
            output = json.loads((root / 'evidence/binary-analysis.json').read_text())
            self.assertEqual(set(output), {'donation_relay'})
            for field, value in expected.items():
                self.assertEqual(output['donation_relay'][field], value, field)
            self.assertEqual(output['donation_relay']['elf_sha256'],
                             hashlib.sha256(raw[:expected['elf_extent']]).hexdigest())
            inventory = json.loads((root / 'evidence/interface-inventory.json').read_text())
            self.assertEqual(sorted(inventory), ['pump'])
            idl = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
            self.assertEqual(inventory['pump']['address'], idl['address'])

    def test_all_five_captures_are_selected_in_order(self):
        self.assertEqual(analysis.program_names(ROOT),
                         ['pump', 'pump_amm', 'pump_fees', 'mayhem', 'donation_relay'])

    def test_archived_selector_still_controls_programs_and_addresses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'repro').mkdir()
            selected = {'mayhem': 'archive-address', 'donation_relay': 'archive-relay'}
            (root / 'repro/programs.json').write_text(json.dumps(selected))
            with patch.object(analysis, 'ROOT', root):
                self.assertEqual(analysis.program_names(), selected)
                self.assertEqual(analysis.program_addresses(), selected)
            self.assertEqual(analysis.capture_directory(root, 'donation_relay'),
                             root / 'evidence/dependencies/donation_relay')
            self.assertEqual(analysis.capture_directory(root, 'mayhem'),
                             root / 'evidence/original/mayhem')


if __name__ == '__main__':
    unittest.main(verbosity=2)
