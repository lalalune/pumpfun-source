#!/usr/bin/env python3
"""Only r10 (frame pointer) operands may classify a difference as 'frame'."""
import contextlib, importlib.util, io, json, struct, sys, tempfile, unittest
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
SPEC = importlib.util.spec_from_file_location('window_triage', H / 'triage.py')
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)


def insn(op, dst, src, off, imm=0):
    return struct.pack('<BBhi', op, (src << 4) | dst, off, imm)


def body(*slots):
    return b''.join(insn(*s) for s in slots)


def classify(original, candidate):
    """Run main() on one synthetic window and return its category."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cand = tmp / 'cand.so'; cand.write_bytes(b'ELF')
        out = tmp / 'triage.json'
        triage.sections = lambda blob: {'.text': {'addr': 0x1000, 'offset': 0, 'size': len(candidate)}}
        triage.score = lambda p: {0x1000: {'normalized': False}}
        triage.candidate_functions = lambda p: [(0x1000, len(candidate), '_ZN4testE')]
        triage.original_windows = lambda: [{'start': 0x1000, 'bytes': len(original), 'raw': original}]
        triage.sites = lambda blob, secs, start, raw: []
        triage.normalize = lambda raw, addr, secs: raw
        triage.body = lambda blob, secs, addr, size: candidate
        triage.demangle = lambda name: name
        argv = sys.argv
        sys.argv = ['triage.py', '--cand', str(cand), '--json', str(out)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                triage.main()
        finally:
            sys.argv = argv
        return json.loads(out.read_text())[0]['category']


class FrameClassificationTests(unittest.TestCase):
    def test_scratch_register_constant_is_not_frame(self):
        # mov64 r6, imm: a constant in a scratch register, no r10 access.
        before = body(*[(0xb7, 6, 0, 0, 100 + i) for i in range(5)])
        after = body(*[(0xb7, 6, 0, 0, 200 + i) for i in range(5)])
        self.assertEqual(classify(before, after), 'equal-len')

    def test_stack_slot_is_frame(self):
        before = body(*[(0x7b, 10, 1, -8 - 8 * i) for i in range(5)])
        after = body(*[(0x7b, 10, 1, -16 - 8 * i) for i in range(5)])
        self.assertEqual(classify(before, after), 'frame')

    def test_only_r10_alu_writes_are_frame(self):
        # add64 r10, -N adjusts the frame; add64 r6, N does not.
        r10 = classify(body(*[(0x07, 10, 10, -8 * i) for i in range(5)]),
                       body(*[(0x07, 10, 10, -8 * i - 1) for i in range(5)]))
        r6 = classify(body(*[(0x07, 6, 6, 8 * i) for i in range(5)]),
                      body(*[(0x07, 6, 6, 8 * i + 1) for i in range(5)]))
        self.assertEqual((r10, r6), ('frame', 'equal-len'))

    def test_only_r10_loads_are_frame(self):
        # ldxdw r1, [r10-8] reads the frame; [r6-8] reads a scratch pointer.
        r10 = classify(body(*[(0x79, 1, 10, -8 - 8 * i) for i in range(5)]),
                       body(*[(0x79, 1, 10, -16 - 8 * i) for i in range(5)]))
        r6 = classify(body(*[(0x79, 1, 6, -8 - 8 * i) for i in range(5)]),
                      body(*[(0x79, 1, 6, -16 - 8 * i) for i in range(5)]))
        self.assertEqual((r10, r6), ('frame', 'equal-len'))


class TriageReportTests(unittest.TestCase):
    def test_missing_parent_directory_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'current' / 'triage.json'
            triage.write_report(path, [{'start': '0x120'}])
            self.assertEqual(path.read_text(), '[\n {\n  "start": "0x120"\n }\n]')

    def test_existing_directory_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'triage.json'
            triage.write_report(path, [])
            triage.write_report(path, [])
            self.assertEqual(path.read_text(), '[]')


if __name__ == '__main__':
    unittest.main()
