"""scripts/analyze.py must write interface-inventory.json in a stable order.

Path.glob() yields directory entries in filesystem order, so the regenerated
inventory's key order (and therefore the committed evidence bytes) used to vary
between machines. The IDLs are now read in sorted order. This test points the
analyzer at a temporary tree and feeds glob results in two different orders.

Run from the repository root: python3 -I -B scripts/test_analyze_inventory_order.py
"""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyze  # noqa: E402

IDL_NAMES = ('pump', 'pump_amm', 'pump_fees')


def write_idls(root):
    upstream = root / 'evidence' / 'upstream'
    upstream.mkdir(parents=True)
    for name in IDL_NAMES:
        (upstream / f'{name}.json').write_text(json.dumps({
            'address': f'{name}-address', 'metadata': {'name': name},
            'instructions': [{'name': 'ix', 'accounts': [{'name': 'system_program', 'address': '11111111111111111111111111111111'}]}],
        }))


def run_with_glob_order(reverse):
    real_glob = pathlib.Path.glob

    def ordered_glob(self, pattern):
        return iter(sorted(real_glob(self, pattern), reverse=reverse))

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        write_idls(root)
        with mock.patch.object(analyze, 'ROOT', root), \
                mock.patch.object(analyze, 'program_names', return_value=[]), \
                mock.patch.object(pathlib.Path, 'glob', ordered_glob), \
                contextlib.redirect_stdout(io.StringIO()):
            analyze.analyze()
        return (root / 'evidence' / 'interface-inventory.json').read_bytes()


class InventoryOrderTests(unittest.TestCase):
    def test_output_independent_of_glob_order(self):
        self.assertEqual(run_with_glob_order(False), run_with_glob_order(True))

    def test_programs_written_in_sorted_order(self):
        keys = list(json.loads(run_with_glob_order(True)))
        self.assertEqual(keys, sorted(IDL_NAMES))


if __name__ == '__main__':
    unittest.main()
