"""Select reported or demangled symbols; reject patterns with no candidate."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('census_blocksim', HERE / 'blocksim.py')
blocksim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blocksim)

EXIT = (b'\x95' + bytes(7))
WINDOW = {'start': 0x1000, 'bytes': 8, 'raw': EXIT}


class FakeCandidate:
    funcs = [(0x2000, 8, 'pump5other17h0123456789abcdefE')]
    secs = {}

    def __init__(self, path):
        self.path = path

    def fn(self, start, size):
        return EXIT


class SymbolSelectionTests(unittest.TestCase):
    def run_main(self, pattern):
        argv = ['blocksim.py', 'candidate.so', '0x1000', '--sym', pattern]
        stdout = io.StringIO()
        with (mock.patch.object(sys, 'argv', argv),
              mock.patch.object(blocksim, 'original_windows', return_value=[WINDOW]),
              mock.patch.object(blocksim, 'Cand', FakeCandidate),
              mock.patch.object(blocksim, 'demangle', side_effect=lambda name: name),
              mock.patch.object(blocksim, 'normalize', side_effect=lambda raw, addr, secs: raw),
              contextlib.redirect_stdout(stdout)):
            try:
                blocksim.main()
            except SystemExit as stop:
                return stop.code, stdout.getvalue()
        return 0, stdout.getvalue()

    def test_matching_symbol_prints_one_comparison(self):
        code, output = self.run_main('other')
        self.assertEqual(code, 0)
        self.assertEqual(output.count("'block_jaccard'"), 1)

    def test_unmatched_symbol_is_a_failure(self):
        code, output = self.run_main('no_such_function')
        self.assertEqual(output, '')
        self.assertNotIn(code, (0, None), 'an unmatched --sym exited successfully')
        self.assertIn('no_such_function', str(code))


def captured_symbol_fixture(blob, start, size, symbol):
    """Add a retained symbol to a disposable capture copy without changing code."""
    output = bytearray(blob)
    shoff = struct.unpack_from('<Q', output, 40)[0]
    count, names_index = struct.unpack_from('<HH', output, 60)
    headers = [list(struct.unpack_from('<IIQQQQIIQQ', output, shoff + i * 64)) for i in range(count)]
    names_header = headers[names_index]
    names = output[names_header[4]:names_header[4] + names_header[5]]
    string_name, symbol_name = len(names), len(names) + len(b'.strtab\0')
    names.extend(b'.strtab\0.symtab\0')
    names_header[4], names_header[5] = len(output), len(names)
    output.extend(names)
    strings = b'\0' + symbol.encode() + b'\0'
    headers.append([string_name, 3, 0, 0, len(output), len(strings), 0, 0, 1, 0])
    output.extend(strings)
    output.extend(bytes(-len(output) % 8))
    text_index = next(i for i, h in enumerate(headers) if names[h[0]:].split(b'\0', 1)[0] == b'.text')
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, text_index, start, size)
    headers.append([symbol_name, 2, 0, 0, len(output), len(symbols), count, 1, 8, 24])
    output.extend(symbols)
    new_shoff = len(output)
    for header in headers:
        output.extend(struct.pack('<IIQQQQIIQQ', *header))
    struct.pack_into('<Q', output, 40, new_shoff)
    struct.pack_into('<H', output, 60, len(headers))
    return output


class ReportedSymbolTests(unittest.TestCase):
    def test_scorer_symbol_and_demangled_name_select_the_same_comparison(self):
        root = HERE.parents[3]
        start = 0x120580
        record = json.loads((root / 'reconstruction/pump-main/baseline/score.json').read_text())['windows'][str(start)]
        symbol = record['symbols'][0]
        capture = root / 'evidence/original/pump/deployed.so'
        original = capture.read_bytes()
        with tempfile.TemporaryDirectory(prefix='pump-blocksim-symbol-') as directory:
            candidate, report = Path(directory) / 'candidate.so', Path(directory) / 'score.json'
            candidate.write_bytes(captured_symbol_fixture(original, start, record['bytes'], symbol))
            score = subprocess.run([sys.executable, '-B', str(root / 'reconstruction/harness/score.py'),
                                    str(candidate), '--no-baseline', '--json', str(report)],
                                   capture_output=True, text=True)
            self.assertEqual(score.returncode, 0, score.stdout + score.stderr)
            reported = json.loads(report.read_text())['windows'][str(start)]['symbols'][0]
            outputs = []
            for pattern in (re.escape(reported), re.escape(blocksim.demangle(reported))):
                result = subprocess.run([sys.executable, '-B', str(HERE / 'blocksim.py'), str(candidate),
                                         hex(start), '--sym', pattern], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("'block_jaccard': 1.0", result.stdout)
                outputs.append(result.stdout)
            self.assertEqual(outputs[0], outputs[1])
            missing = subprocess.run([sys.executable, '-B', str(HERE / 'blocksim.py'), str(candidate),
                                      hex(start), '--sym', 'no_such_function'], capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertEqual(missing.stdout, '')
        self.assertEqual(capture.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
