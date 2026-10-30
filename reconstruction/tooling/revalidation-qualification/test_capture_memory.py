"""Real verifier output must retain its receipt without loading the whole log."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import tracemalloc
import unittest

SPEC = importlib.util.spec_from_file_location('capture_memory_audit', Path(__file__).with_name('audit.py'))
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
REPO = Path(__file__).resolve().parents[3]


class CaptureMemoryTests(unittest.TestCase):
    def test_large_real_verifier_preserves_output_hash_and_bounded_tail_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            (packet / 'verify.py').write_text(
                "import sys\n"
                "for _ in range(256):\n"
                "    sys.stdout.buffer.write(b'x' * 65536)\n"
                "sys.stdout.buffer.write(b'\\xff\\xf0\\x9f\\x98\\x80tail\\n')\n",
                encoding='utf-8')
            expected_hash = hashlib.sha256()
            for _ in range(256):
                expected_hash.update(b'x' * 65536)
            expected_hash.update(b'\xff\xf0\x9f\x98\x80tail\n')
            frozen = audit.load_frozen(REPO)
            tracemalloc.start()
            try:
                result = audit.run_verifier(frozen, REPO, packet, 15, 0.1)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            self.assertEqual(result['status'], 'pass', result)
            self.assertEqual(result['output_bytes'], 16 * 1024 * 1024 + 10)
            self.assertEqual(result['output_sha256'], expected_hash.hexdigest())
            self.assertEqual(result['output'], 'x' * 1993 + '\ufffd\U0001f600tail')
            self.assertTrue(result['output_truncated'])
            # An allocation budget, not a timing/RSS assertion: the 16 MiB
            # stdout file must not become one resident Python bytes/string.
            self.assertLess(peak, 2 * 1024 * 1024, f'Python allocation peak: {peak}')

    def test_incremental_utf8_and_character_tail_match_whole_decode(self):
        cases = (b'', b'  short\r\n', b'x' * 65535 + '\u20ac'.encode() + b'end',
                 b'x' * 65535 + b'\xf0\x9f', b'\xff' * 2001,
                 '\U0001f600'.encode() * 2000, b' ' * 2001)
        for raw in cases:
            with self.subTest(length=len(raw)), tempfile.TemporaryFile() as capture:
                capture.write(raw)
                actual = audit.read_capture(capture)
            decoded = raw.decode('utf-8', errors='replace')
            self.assertEqual(actual, {
                'output': decoded[-2000:].strip(), 'output_bytes': len(raw),
                'output_sha256': hashlib.sha256(raw).hexdigest(),
                'output_truncated': len(decoded) > 2000})


if __name__ == '__main__':
    unittest.main()
