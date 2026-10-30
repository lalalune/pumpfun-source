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
    candidates = candidate if isinstance(candidate, list) else [candidate]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cand = tmp / 'cand.so'; cand.write_bytes(b'ELF')
        out = tmp / 'triage.json'
        triage.sections = lambda blob: {'.text': {'addr': 0x1000, 'offset': 0, 'size': sum(map(len, candidates))}}
        triage.score = lambda p: {0x1000: {'normalized': False}}
        triage.function_symbols = lambda blob: [(0x1000 + i * 0x1000, len(raw), f'candidate-{i}')
                                               for i, raw in enumerate(candidates)]
        triage.original_windows = lambda: [{'start': 0x1000, 'bytes': len(original), 'raw': original}]
        triage.sites = lambda blob, secs, start, raw: []
        triage.normalize = lambda raw, addr, secs: raw
        triage.body = lambda blob, secs, addr, size: candidates[(addr - 0x1000) // 0x1000]
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

    def test_non_frame_changes_at_stack_instructions_are_not_frame(self):
        original = body(*[(0x7b, 10, 1, -8 - 8 * i) for i in range(5)])
        candidates = {
            'source register': [(0x7b, 10, 2, -8 - 8 * i) for i in range(5)],
            'opcode': [(0x63, 10, 1, -8 - 8 * i) for i in range(5)],
            'base register': [(0x7b, 6, 1, -8 - 8 * i) for i in range(5)],
        }
        for label, instructions in candidates.items():
            with self.subTest(change=label):
                self.assertEqual(classify(original, body(*instructions)), 'equal-len')
        original = body(*[(0x7a, 10, 0, -8 - 8 * i, 1) for i in range(5)])
        changed = body(*[(0x7a, 10, 0, -8 - 8 * i, 2) for i in range(5)])
        self.assertEqual(classify(original, changed), 'equal-len')

    def test_classification_uses_best_candidate_not_last_scanned(self):
        original = body(*[(0x7b, 10, 1, -8 - 8 * i) for i in range(6)])
        five_frame_changes = body(*[(0x7b, 10, 1, -16 - 8 * i) if i < 5 else (0x7b, 10, 1, -8 - 8 * i)
                                    for i in range(6)])
        six_nonframe_changes = body(*[(0x7b, 10, 2, -8 - 8 * i) for i in range(6)])
        self.assertEqual(classify(original, [five_frame_changes, six_nonframe_changes]), 'frame')
        five_nonframe_changes = body(*[(0x7b, 10, 2, -8 - 8 * i) if i < 5 else (0x7b, 10, 1, -8 - 8 * i)
                                       for i in range(6)])
        six_frame_changes = body(*[(0x7b, 10, 1, -16 - 8 * i) for i in range(6)])
        self.assertEqual(classify(original, [five_nonframe_changes, six_frame_changes]), 'equal-len')

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

    def test_stack_address_offsets_are_frame(self):
        # mov64 r1, r10; add64 r1, -N forms a stack-slot address (SBF v1 idiom).
        def window(offsets, src=10, dst=1):
            slots = []
            for n in offsets:
                slots += [(0xbf, dst, src, 0), (0x07, dst, 0, 0, n)]
            return body(*slots)
        frame = classify(window([-8, -16, -24, -32]), window([-16, -24, -32, -40]))
        # Controls: copying r6 instead of r10, or adding to a different register.
        scratch = classify(window([-8, -16, -24, -32], src=6), window([-16, -24, -32, -40], src=6))
        mixed = classify(body(*[s for n in (-8, -16, -24, -32) for s in ((0xbf, 2, 10, 0), (0x07, 1, 0, 0, n))]),
                         body(*[s for n in (-16, -24, -32, -40) for s in ((0xbf, 2, 10, 0), (0x07, 1, 0, 0, n))]))
        self.assertEqual((frame, scratch, mixed), ('frame', 'equal-len', 'equal-len'))

    def test_frame_address_requires_adjacent_copy(self):
        raw = body((0xbf, 1, 10, 0), (0x07, 1, 0, 0, -8), (0x07, 1, 0, 0, -8))
        self.assertTrue(triage.frame_slot(raw, 8))
        self.assertFalse(triage.frame_slot(raw, 16))
        self.assertFalse(triage.frame_slot(raw, 0))
        self.assertFalse(triage.frame_slot(body((0x07, 1, 0, 0, -8)), 0))


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


class TriageReportBytesTests(unittest.TestCase):
    def test_report_bytes_do_not_follow_the_host_line_ending(self):
        from unittest.mock import patch
        original_open = Path.open
        def windows_open(path, mode='r', *args, **kwargs):
            if 'b' not in mode and any(flag in mode for flag in 'wax'):
                if kwargs.get('newline') is None:
                    kwargs['newline'] = '\r\n'
            return original_open(path, mode, *args, **kwargs)
        rows = [{'symbol': 'sample', 'category': 'equal-len'}]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'triage.json'
            with patch.object(Path, 'open', windows_open):
                triage.write_report(output, rows)
            self.assertEqual(output.read_bytes(), json.dumps(rows, indent=1).encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
