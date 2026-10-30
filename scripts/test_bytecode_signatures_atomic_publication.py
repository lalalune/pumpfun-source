"""Bytecode-signature packets are staged before their final publication."""
import contextlib
import hashlib
import io
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import bytecode_signatures as tool
import deep_disassembly as publisher


def generate(output):
    with mock.patch.object(sys, 'argv', [
            'bytecode_signatures.py', '--output', str(output)]), \
            contextlib.redirect_stdout(io.StringIO()):
        tool.main()


def packet_hashes(output):
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.iterdir()
    }


class BytecodeSignaturesAtomicPublicationTests(unittest.TestCase):
    def test_copied_read_only_helpers_do_not_load_packet_publisher(self):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / 'scripts'
            scripts.mkdir()
            for name in ('bytecode_signatures.py', 'window_elf_reader.py'):
                shutil.copyfile(SCRIPTS / name, scripts / name)
            code = (
                "import sys; from types import SimpleNamespace; "
                "sys.path.insert(0, sys.argv[1]); import bytecode_signatures as b; "
                "rows=b.detect_cpi_patterns(SimpleNamespace(b=bytes(8), relocations={}),0,8); "
                "raise SystemExit(0 if rows==[] and 'deep_disassembly' not in sys.modules else 1)"
            )
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(scripts)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_late_write_failure_leaves_no_partial_new_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet'
            real_write_text = Path.write_text

            def fail_readme(path, *args, **kwargs):
                if path.name == 'README.md':
                    raise OSError('injected README write failure')
                return real_write_text(path, *args, **kwargs)

            with mock.patch.object(Path, 'write_text', fail_readme):
                with self.assertRaisesRegex(OSError, 'injected README write failure'):
                    generate(output)

            self.assertFalse(output.exists(), 'failed analysis published a partial packet')
            self.assertEqual(list(output.parent.glob('.packet.staging-*')), [])

    def test_failed_regeneration_preserves_prior_complete_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet'
            generate(output)
            before = packet_hashes(output)
            real_write_text = Path.write_text

            def fail_top_ngrams(path, *args, **kwargs):
                if path.name == 'top-ngrams.json':
                    raise OSError('injected regeneration write failure')
                return real_write_text(path, *args, **kwargs)

            with mock.patch.object(Path, 'write_text', fail_top_ngrams):
                with self.assertRaisesRegex(OSError, 'injected regeneration write failure'):
                    generate(output)

            self.assertEqual(packet_hashes(output), before)
            self.assertEqual(list(output.parent.glob('.packet.staging-*')), [])

    def test_native_publish_does_not_replace_a_late_empty_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet'
            rename = publisher.rename_directory
            def competing_writer(source, destination, **kwargs):
                output.mkdir()
                return rename(source, destination, **kwargs)
            with mock.patch.object(publisher, 'rename_directory', competing_writer):
                with self.assertRaises(FileExistsError):
                    generate(output)
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(output.parent.glob('.packet.staging-*')), [])

    def test_replacement_preserves_old_packet_late_files_and_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet'
            generate(output)
            before = packet_hashes(output)
            output.chmod(0o700)
            build = tool._build_packet
            def competing_writer(*args):
                result = build(*args)
                (output / 'late.txt').write_bytes(b'late evidence')
                return result
            with mock.patch.object(tool, '_build_packet', competing_writer):
                generate(output)
            previous = list(output.parent.glob('.packet.previous-*'))
            self.assertEqual(len(previous), 1)
            after = packet_hashes(previous[0])
            self.assertEqual({name: after[name] for name in before}, before)
            self.assertEqual((previous[0] / 'late.txt').read_bytes(), b'late evidence')
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)


if __name__ == '__main__':
    unittest.main()
