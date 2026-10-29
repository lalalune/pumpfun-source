#!/usr/bin/env python3
"""The original-window cache must follow original.so and functions.tsv.

A pickle left in reconstruction/base is reused with no input check. After the
window table or captured program changes, scoring keeps the previous bodies.

Made via @slopdotcash
AI provider/model: SpaceXAI / grok-4.7-high-fast
Client / agent tooling: Cursor
Contribution skill revision: N/A - ordinary GitHub contribution without optional run evidence
Attribution status: self-reported
— [contributor]
<!-- slop-contribution-attribution:v1 {"provider":"SpaceXAI","model":"grok-4.7-high-fast","client":"Cursor","skill_revision":"N/A - ordinary GitHub contribution without optional run evidence"} -->
"""
import pickle
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import score  # noqa: E402


def elf_with_text(text):
    """Minimal ELF64 whose .text file bytes are `text` and whose address matches."""
    string_table = b'\0.text\0.shstrtab\0'
    text_offset = 64
    strings_offset = text_offset + len(text)
    shoff = strings_offset + len(string_table)
    header = bytearray(64)
    header[0:4] = b'\x7fELF'
    header[4] = 2
    header[5] = 1
    header[6] = 1
    struct.pack_into(
        '<HHIQQQIHHHHHH', header, 16,
        1, 0xF7, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 3, 2,
    )
    def shdr(name, kind, addr, offset, size):
        return struct.pack('<IIQQQQIIQQ', name, kind, 0, addr, offset, size, 0, 0, 1, 0)
    headers = b''.join((
        shdr(0, 0, 0, 0, 0),
        shdr(1, 1, text_offset, text_offset, len(text)),
        shdr(7, 3, 0, strings_offset, len(string_table)),
    ))
    return bytes(header) + text + string_table + headers


class OriginalWindowCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.text = b'\x95' * 8 + b'\x05' * 8
        (self.base / 'original.so').write_bytes(elf_with_text(self.text))
        (self.base / 'functions.tsv').write_text(
            'program\tvariant\toriginal_start\toriginal_end\n'
            'pump\tselected\t64\t80\n'
            'pump\tdraft\t64\t80\n',
            encoding='utf-8',
        )
        self.previous = score.BASE
        score.BASE = self.base
        score._INPUT_DIGESTS.clear()

    def tearDown(self):
        score.BASE = self.previous
        score._INPUT_DIGESTS.clear()
        self.tmp.cleanup()

    def test_stale_pickle_does_not_replace_the_current_window_table(self):
        cache = self.base / 'original-windows.pkl'
        cache.write_bytes(pickle.dumps([
            {'start': 999, 'bytes': 1, 'raw': b'STALE', 'norm': b'STALE'},
        ]))
        rows = score.original_windows()
        self.assertEqual([row['start'] for row in rows], [64])
        self.assertEqual(rows[0]['raw'], self.text)
        self.assertNotEqual(rows[0]['raw'], b'STALE')

    def test_matching_stamp_reuses_the_cache_and_a_new_table_rebuilds(self):
        first = score.original_windows()
        self.assertEqual(first[0]['start'], 64)
        cached = pickle.loads((self.base / 'original-windows.pkl').read_bytes())
        cached[0]['marker'] = 'cached'
        (self.base / 'original-windows.pkl').write_bytes(pickle.dumps(cached))
        second = score.original_windows()
        self.assertEqual(second[0].get('marker'), 'cached')

        (self.base / 'functions.tsv').write_text(
            'program\tvariant\toriginal_start\toriginal_end\n'
            'pump\tselected\t64\t72\n',
            encoding='utf-8',
        )
        third = score.original_windows()
        self.assertNotIn('marker', third[0])
        self.assertEqual(third[0]['start'], 64)
        self.assertEqual(third[0]['bytes'], 8)
        self.assertEqual(third[0]['raw'], self.text[:8])

    def test_attribute_error_from_a_corrupt_pickle_rebuilds(self):
        score.original_windows()
        class Missing:
            def __reduce__(self):
                return (getattr, (object, 'missing_cache_field'))
        payload = pickle.dumps(Missing())
        with self.assertRaises(AttributeError):
            pickle.loads(payload)
        (self.base / 'original-windows.pkl').write_bytes(payload)
        rows = score.original_windows()
        self.assertEqual([row['start'] for row in rows], [64])
        self.assertEqual(rows[0]['raw'], self.text)

    def test_keyboard_interrupt_and_system_exit_propagate(self):
        score.original_windows()
        cache = self.base / 'original-windows.pkl'
        preserved = cache.read_bytes()
        for exc in (KeyboardInterrupt, SystemExit):
            with mock.patch.object(score.pickle, 'loads', side_effect=exc):
                with self.assertRaises(exc):
                    score.original_windows()
            self.assertEqual(cache.read_bytes(), preserved)

    def test_minimal_elf_is_parsed_by_sections_body_and_normalize(self):
        text = struct.pack('<BBhi', 0x18, 0x00, 0, 64) + struct.pack('<BBHI', 0, 0, 0, 0)
        blob = elf_with_text(text)
        secs = score.sections(blob)
        self.assertIn('.text', secs)
        self.assertIn('.shstrtab', secs)
        self.assertEqual(secs['.text'], {'addr': 64, 'offset': 64, 'size': len(text)})
        self.assertEqual(secs['.shstrtab']['addr'], 0)
        self.assertGreater(secs['.shstrtab']['size'], 0)
        raw = score.body(blob, secs, 64, len(text))
        self.assertEqual(raw, text)
        norm = score.normalize(raw, 64, secs)
        self.assertEqual(len(norm), len(text))
        self.assertEqual(norm[0], 0x18)
        self.assertEqual(norm[4:8], b'\x00\x00\x00\x00')
        self.assertEqual(norm[12:16], b'\x00\x00\x00\x00')
        self.assertNotEqual(norm, raw)

    def test_unchanged_inputs_reuse_the_content_hash(self):
        first = score.window_cache_stamp()
        reads = {'n': 0}
        original = Path.read_bytes

        def counting(self, *args, **kwargs):
            reads['n'] += 1
            return original(self, *args, **kwargs)

        with mock.patch.object(Path, 'read_bytes', counting):
            second = score.window_cache_stamp()
        self.assertEqual(second, first)
        self.assertEqual(reads['n'], 0)
        (self.base / 'functions.tsv').write_text(
            'program\tvariant\toriginal_start\toriginal_end\n'
            'pump\tselected\t64\t72\n',
            encoding='utf-8',
        )
        self.assertNotEqual(score.window_cache_stamp(), first)


if __name__ == '__main__':
    unittest.main()
