"""Exercise the pairing CLI with the real ranking implementation and 12 bodies."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import pair_candidates
import score
import win

class PairingLimitTests(unittest.TestCase):
    def run_cli(self, top, selected=None):
        raw = b''.join(struct.pack('<BBhi', op, 0, 0, imm)
                       for op, imm in [(0xb7, 1), (0x07, 2), (0x95, 0)])
        candidate = win.Cand.__new__(win.Cand)
        candidate.__dict__.update(_opgrams={}, _tokens={}, blob=raw, secs={},
            funcs=[(i * 32, len(raw), f'fn_{i}') for i in range(12)], fn=lambda s, n: raw)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'candidate.so'; path.write_bytes(raw)
            argv = [str(path), '0', '--top', str(top)]
            if selected: argv += ['--select-symbol', selected]
            with patch.object(win, 'Cand', return_value=candidate), patch.object(score, 'original_windows',
                    return_value=[{'start': 0, 'bytes': len(raw), 'raw': raw}]), contextlib.redirect_stdout(io.StringIO()) as output:
                pair_candidates.main(argv)
            return json.loads(output.getvalue())

    def test_expanded_search_can_select_candidate_outside_first_eight(self):
        report = self.run_cli(12, 'fn_0')
        self.assertEqual(len(report['candidates']), 12)
        self.assertEqual(report['selected']['symbol'], 'fn_0')
        self.assertEqual(report['selection'], 'explicit-symbol')

    def test_available_candidates_bound_results(self):
        self.assertEqual(len(self.run_cli(100)['candidates']), 12)
        self.assertEqual(len(self.run_cli(3)['candidates']), 3)

    def test_invalid_limits_rejected(self):
        for limit in [0, -1]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                self.run_cli(limit)
            self.assertEqual(cm.exception.code, 2)

if __name__ == '__main__': unittest.main()
