"""Fault-injection checks for disassembly snapshots and round-trip admission."""
import contextlib
import gzip
import io
import json
from pathlib import Path
import struct
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sbpf_disassembly_inventory as inventory
import sbpf_disassembly_roundtrip as roundtrip


class AdmittedDisassemblyInputs(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.tool = self.root / 'tool/target/release/sbpf'
        self.tool.parent.mkdir(parents=True)
        self.tool.write_bytes(b'admitted executable')
        self.tool.chmod(0o700)
        (self.root / 'tool/Cargo.lock').write_text('fixture')
        self.original = self.root / 'original.so'
        self.original.write_bytes(bytes(64) + struct.pack('<BBhi', 0x95, 0, 0, 0))
        self.inputs = self.root / 'inventory'
        self.inputs.mkdir()
        self.record = {'input': 'original.so', 'input_sha256': inventory.sha(self.original.read_bytes()),
                       'instructions': [{'file_offset': 64, 'opcode': 0x95, 'src': 0,
                                         'immediate': 0, 'assembly': 'exit'}]}
        self.entry = self.save_record()
        self.manifest = {'programs': [self.entry], 'tool_sha256': inventory.sha(self.tool.read_bytes()),
                         'tool_revision': 'fixture'}

    def save_record(self):
        data = gzip.compress(json.dumps(self.record).encode())
        (self.inputs / 'pump.json.gz').write_bytes(data)
        return {'name': 'pump', 'inventory_sha256': inventory.sha(data)}

    @staticmethod
    def sections(data):
        return {'.text': (0, 1, 6, 64, 64, len(data) - 64, 0, 0, 8, 0)}

    def run_roundtrip(self, worker=None):
        (self.inputs / 'manifest.json').write_text(json.dumps(self.manifest))
        output = self.root / 'roundtrip'
        argv = ['roundtrip', '--tool-source', str(self.root / 'tool'), '--inventory', str(self.inputs),
                '--output', str(output)]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
            if worker is None:
                roundtrip.main()
            else:
                with patch.object(roundtrip, 'roundtrip', side_effect=worker):
                    roundtrip.main()
        return output

    def test_disassembler_reads_the_same_elf_bytes_as_recorded_provenance(self):
        admitted = self.original.read_bytes()
        observed = []
        def run(command, **kwargs):
            self.original.write_bytes(bytes(64) + struct.pack('<BBhi', 0x07, 1, 0, 1))
            data = Path(command[2]).read_bytes()
            observed.append(data)
            return subprocess.CompletedProcess(command, 0, b'exit\n' if data == admitted else b'add64 r1, 0x1\n', b'')
        output = self.root / 'out'
        output.mkdir()
        with patch.object(inventory, 'ROOT', self.root), patch.object(inventory, 'sections', self.sections), \
                patch.object(inventory.subprocess, 'run', run):
            receipt = inventory.inventory(self.tool, 'pump', self.original, output)
        self.assertEqual(observed, [admitted])
        self.assertEqual(receipt['input_sha256'], inventory.sha(admitted))
        saved = json.loads(gzip.decompress((output / 'pump.json.gz').read_bytes()))
        self.assertEqual(saved['instructions'][0]['assembly'], 'exit')

    def test_unsafe_and_conflicting_names_fail_before_workers(self):
        for names in [['pump', 'pump'], ['pump', 'PUMP'], ['../escape'], ['/absolute'],
                       ['C:\\escape'], ['report.json'], ['.'], [''], ['x/y'],
                       ['NUL'], ['con'], ['Lpt9.txt'], ['bad?name'], ['bad*name'],
                       ['bad|name'], ['bad<name'], ['bad\"name'], ['bad\x7fname']]:
            with self.subTest(names=names):
                shutil.rmtree(self.root / 'roundtrip', ignore_errors=True)
                self.manifest['programs'] = [{'name': name} for name in names]
                calls = []
                def worker(_tool, _inventory, entry, _output):
                    calls.append(entry['name'])
                    return {'name': entry['name'], 'full_text_equality': True}
                with self.assertRaises(ValueError):
                    self.run_roundtrip(worker)
                self.assertEqual(calls, [])
                self.assertFalse((self.root / 'roundtrip').exists())

    def assembler(self, command, **kwargs):
        folder = Path(command[command.index('--deploy-dir') + 1])
        folder.mkdir(parents=True)
        (folder / 'reference-derived.so').write_bytes(self.original.read_bytes())
        return subprocess.CompletedProcess(command, 0, b'', b'')

    def test_raw_bytes_directives_and_multiline_assembly_cannot_count_as_instructions(self):
        for asm in ['.byte 0x95,0,0,0,0,0,0,0', '.quad 0x95', '.include "other.s"',
                    'exit\n.byte 0', 'exit\n', 'exit\r\n', 'label: exit', 'exit; .byte 0',
                    'exit\u2028.byte 0']:
            with self.subTest(assembly=asm):
                self.record['instructions'][0]['assembly'] = asm
                entry = self.save_record()
                output = self.root / ('out-' + str(len(asm)))
                shutil.rmtree(output, ignore_errors=True)
                output.mkdir(exist_ok=True)
                with patch.object(roundtrip, 'ROOT', self.root), patch.object(roundtrip, 'sections', self.sections), \
                        patch.object(roundtrip.subprocess, 'run', side_effect=self.assembler) as run:
                    with self.assertRaisesRegex(ValueError, 'instruction'):
                        roundtrip.roundtrip(self.tool, self.inputs, entry, output)
                    run.assert_not_called()

    def test_valid_instruction_only_roundtrip_is_preserved(self):
        output = self.root / 'out'
        output.mkdir()
        with patch.object(roundtrip, 'ROOT', self.root), patch.object(roundtrip, 'sections', self.sections), \
                patch.object(roundtrip.subprocess, 'run', side_effect=self.assembler):
            result = roundtrip.roundtrip(self.tool, self.inputs, self.entry, output)
        self.assertTrue(result['full_text_equality'])
        self.assertEqual((output / 'pump/reference-derived.s').read_bytes(), b'exit\n')

    def test_roundtrip_workers_use_the_admitted_tool_after_original_path_replacement(self):
        admitted = self.tool.read_bytes()
        observed = []
        def worker(tool, _inventory, entry, _output):
            self.tool.write_bytes(b'replacement executable')
            observed.append(Path(tool).read_bytes())
            return {'name': entry['name'], 'full_text_equality': True}
        output = self.run_roundtrip(worker)
        self.assertEqual(observed, [admitted])
        self.assertEqual(json.loads((output / 'report.json').read_text())['tool_sha256'], inventory.sha(admitted))

    def test_report_hash_binds_the_manifest_admitted_before_workers(self):
        admitted = json.dumps(self.manifest).encode()
        def worker(tool, inputs, entry, output):
            (inputs / 'manifest.json').write_text('{"changed": true}')
            return {'name': entry['name'], 'full_text_equality': True}
        output = self.run_roundtrip(worker)
        report = json.loads((output / 'report.json').read_text())
        self.assertEqual(report['inventory_manifest_sha256'], inventory.sha(admitted))

    def test_inventory_workers_and_version_use_the_same_admitted_tool(self):
        admitted = self.tool.read_bytes()
        observed = []
        def worker(tool, name, _input, _output):
            observed.append(Path(tool).read_bytes())
            self.tool.write_bytes(b'replacement executable')
            return {'name': name}
        def command(args, **kwargs):
            if args[-1] == 'HEAD':
                return 'fixture\n'
            if args[-1] == '--version':
                observed.append(Path(args[0]).read_bytes())
                return 'fixture-version\n'
            return b''
        output = self.root / 'inventory-output'
        argv = ['inventory', '--tool-source', str(self.root / 'tool'), '--output', str(output)]
        with patch.object(sys, 'argv', argv), patch.object(inventory, 'ROOT', self.root), \
                patch.object(inventory, 'program_inputs', return_value=[('pump', self.original)]), \
                patch.object(inventory, 'inventory', side_effect=worker), \
                patch.object(inventory.subprocess, 'check_output', side_effect=command), \
                contextlib.redirect_stdout(io.StringIO()):
            inventory.main()
        self.assertEqual(observed, [admitted, admitted])
        self.assertEqual(json.loads((output / 'manifest.json').read_text())['tool_sha256'], inventory.sha(admitted))

    def test_changed_private_tool_snapshot_cannot_publish_a_report(self):
        def worker(tool, _inventory, entry, _output):
            Path(tool).chmod(0o700)
            Path(tool).write_bytes(b'changed during execution')
            return {'name': entry['name'], 'full_text_equality': True}
        with self.assertRaisesRegex(ValueError, 'snapshot changed'):
            self.run_roundtrip(worker)
        self.assertFalse((self.root / 'roundtrip').exists())

    @unittest.skipIf(sys.platform == "win32", "POSIX executable fixture")
    def test_private_tool_copy_is_executable_and_ignores_rebuilt_source_path(self):
        self.tool.write_text(f'#!{sys.executable}\nprint("admitted-version")\n')
        self.tool.chmod(0o700)
        admitted = self.tool.read_bytes()
        with inventory.tool_snapshot(self.tool) as (executable, digest):
            self.tool.write_text(f'#!{sys.executable}\nprint("replacement-version")\n')
            self.assertEqual(subprocess.check_output([str(executable), '--version']), b'admitted-version\n')
            self.assertEqual(digest, inventory.sha(admitted))
        self.assertFalse(executable.exists())

    def test_generated_call_labels_remain_instruction_only(self):
        self.original.write_bytes(bytes(64) + struct.pack('<BBhi', 0x85, 0x10, 0, -1)
                                  + struct.pack('<BBhi', 0x95, 0, 0, 0))
        self.record['input_sha256'] = inventory.sha(self.original.read_bytes())
        self.record['instructions'] = [
            {'file_offset': 64, 'opcode': 0x85, 'src': 1, 'immediate': -1, 'assembly': 'call -0x1'},
            {'file_offset': 72, 'opcode': 0x95, 'src': 0, 'immediate': 0, 'assembly': 'exit'}]
        entry = self.save_record()
        output = self.root / 'out'
        output.mkdir()
        with patch.object(roundtrip, 'ROOT', self.root), patch.object(roundtrip, 'sections', self.sections), \
                patch.object(roundtrip.subprocess, 'run', side_effect=self.assembler):
            self.assertTrue(roundtrip.roundtrip(self.tool, self.inputs, entry, output)['full_text_equality'])
        self.assertEqual((output / 'pump/reference-derived.s').read_bytes(), b'fn_40:\ncall fn_40\nexit\n')


if __name__ == '__main__':
    unittest.main()
