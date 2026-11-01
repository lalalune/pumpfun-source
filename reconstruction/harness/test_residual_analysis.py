"""Offline synthetic and captured-window coverage for residual_analysis.py."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import residual_analysis as residual
import score


def instruction(opcode, registers=0, displacement=0, immediate=0):
    return struct.pack('<BBhi', opcode, registers, displacement, immediate)


EXIT = instruction(0x95)


def elf_fixture(code, start=0x1000, name='selected'):
    """Build a minimal bounded ELF with one exact STT_FUNC symbol."""
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0'
    strings = b'\0' + name.encode('utf-8') + b'\0'
    names_offset = 384
    text_offset = (names_offset + len(names) + 7) & ~7
    strings_offset = (text_offset + len(code) + 7) & ~7
    symbols_offset = (strings_offset + len(strings) + 7) & ~7
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, 2, start, len(code))
    blob = bytearray(symbols_offset + len(symbols))
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 247, 1)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<I', blob, 48, 0)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<HHH', blob, 58, 64, 5, 1)
    blob[names_offset:names_offset + len(names)] = names
    blob[text_offset:text_offset + len(code)] = code
    blob[strings_offset:strings_offset + len(strings)] = strings
    blob[symbols_offset:symbols_offset + len(symbols)] = symbols
    headers = [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, names_offset, len(names), 0, 0, 1, 0),
        (11, 1, 6, start, text_offset, len(code), 0, 0, 8, 0),
        (17, 3, 0, 0, strings_offset, len(strings), 0, 0, 1, 0),
        (25, 2, 0, 0, symbols_offset, len(symbols), 3, 1, 8, 24),
    ]
    for index, header in enumerate(headers):
        struct.pack_into('<IIQQQQIIQQ', blob, 64 + 64 * index, *header)
    return bytes(blob)


def models(original_code, candidate_code):
    original = residual.load_image_bytes(elf_fixture(original_code), 'original', Path('original.so'))
    candidate = residual.load_image_bytes(elf_fixture(candidate_code), 'candidate', Path('candidate.so'))
    ow = residual.select_window(original, exact_window=(0x1000, len(original_code)))
    cw = residual.select_window(candidate, exact_window=(0x1000, len(candidate_code)))
    om = residual.build_function_model(original, ow)
    cm = residual.build_function_model(candidate, cw)
    graphs = residual.compare_graphs(om, cm)
    classified = residual.classify_residuals(om, cm, graphs['_mapping'])
    return graphs, classified


def captured_symbol_fixture(blob, start, size, symbol):
    """Add one symbol table to a disposable capture copy without changing code."""
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
    strings = b'\0' + symbol.encode('utf-8') + b'\0'
    headers.append([string_name, 3, 0, 0, len(output), len(strings), 0, 0, 1, 0])
    output.extend(strings)
    output.extend(bytes(-len(output) % 8))
    text_index = next(i for i, header in enumerate(headers)
                      if names[header[0]:].split(b'\0', 1)[0] == b'.text')
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, text_index, start, size)
    headers.append([symbol_name, 2, 0, 0, len(output), len(symbols), count, 1, 8, 24])
    output.extend(symbols)
    new_shoff = len(output)
    for header in headers:
        output.extend(struct.pack('<IIQQQQIIQQ', *header))
    struct.pack_into('<Q', output, 40, new_shoff)
    struct.pack_into('<H', output, 60, len(headers))
    return bytes(output)


class InputAdmissionTests(unittest.TestCase):
    def test_exact_candidate_range_must_be_a_function_symbol(self):
        image = residual.load_image_bytes(elf_fixture(EXIT * 2), 'candidate', Path('candidate.so'))
        with self.assertRaisesRegex(ValueError, 'exactly match a function symbol'):
            residual.select_window(image, exact_window=(0x1000, 8))

    def test_malformed_machine_and_lddw_boundary_are_rejected(self):
        malformed = bytearray(elf_fixture(EXIT))
        struct.pack_into('<H', malformed, 18, 62)
        with self.assertRaisesRegex(ValueError, 'EM_BPF or EM_SBPF'):
            residual.load_image_bytes(bytes(malformed), 'original', Path('bad.so'))
        lddw = instruction(0x18) + bytes(8)
        image = residual.load_image_bytes(elf_fixture(lddw), 'original', Path('original.so'))
        with self.assertRaisesRegex(ValueError, 'truncated instruction|logical instruction boundary'):
            residual.select_window(image, exact_window=(0x1000, 8))

    def test_score_receipt_binds_digest_and_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / 'candidate.so'
            candidate_path.write_bytes(elf_fixture(EXIT))
            candidate = residual.load_image(candidate_path, 'candidate')
            original = residual.select_window(
                residual.load_image_bytes(elf_fixture(EXIT), 'original', Path('original.so')),
                exact_window=(0x1000, 8))
            receipt = root / 'score.json'
            receipt.write_text(json.dumps({
                'summary': {'candidate_sha256': candidate['sha256']},
                'windows': {'4096': {'bytes': 8, 'normalized': False, 'raw': False}},
            }), encoding='utf-8')
            admitted = residual.admit_receipt(receipt, candidate, original)
            self.assertEqual(admitted['selected_window']['start'], 0x1000)
            document = json.loads(receipt.read_text())
            document['summary']['candidate_sha256'] = '00' * 32
            receipt.write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'does not match candidate bytes'):
                residual.admit_receipt(receipt, candidate, original)


    def test_score_receipt_identity_and_rows_use_one_read_cohort(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / 'score.json'
            candidate = residual.load_image_bytes(elf_fixture(EXIT), 'candidate', Path('candidate.so'))
            window = {'start': 0x1000, 'size': 8}
            document = {'candidate_sha256': candidate['sha256'],
                        'windows': {'4096': {'bytes': 8, 'normalized': False, 'raw': False}}}
            original = json.dumps(document, indent=2).replace('\n', '\r\n').encode()
            receipt.write_bytes(original)
            real_load = residual.load_report
            def replace_public_then_load(path):
                document['candidate_sha256'] = '0' * 64
                document['windows']['4096'].update(normalized=True, raw=True)
                receipt.write_text(json.dumps(document))
                return real_load(path)
            with patch.object(residual, 'load_report', side_effect=replace_public_then_load):
                admitted = residual.admit_receipt(receipt, candidate, window)
            self.assertEqual(admitted['sha256'], hashlib.sha256(original).hexdigest())
            self.assertFalse(admitted['selected_window']['raw'])
            self.assertFalse(admitted['selected_window']['normalized'])


class SyntheticResidualTests(unittest.TestCase):
    def kinds(self, original, candidate):
        return residual.Counter(row['kind'] for row in models(original, candidate)[1]['ranked'])

    def test_register_opcode_and_call_order_residuals(self):
        self.assertIn('register_usage', self.kinds(instruction(0xb7, 1) + EXIT,
                                                   instruction(0xb7, 2) + EXIT))
        self.assertIn('instruction_sequence', self.kinds(instruction(0xb7) + EXIT,
                                                         instruction(0x07) + EXIT))
        calls = instruction(0x85, immediate=7) + instruction(0x8d, immediate=2) + EXIT
        reordered = instruction(0x8d, immediate=2) + instruction(0x85, immediate=7) + EXIT
        self.assertIn('call_ordering', self.kinds(calls, reordered))

    def test_mapped_branch_shift_is_positional(self):
        original = instruction(0x05, displacement=0) + EXIT
        candidate = instruction(0x05, displacement=1) + instruction(0xb7) + EXIT
        _graphs, report = models(original, candidate)
        rows = report['ranked']
        self.assertTrue(any(row['kind'] == 'block_position_shift' for row in rows))
        self.assertTrue(any(row['kind'] == 'branch_displacement_shift'
                            and row['classification'] == 'positional' for row in rows))
        self.assertTrue(any(row['kind'] == 'unmatched_candidate_block' for row in rows))

    def test_branch_endpoint_change_is_structural(self):
        original = instruction(0x15, displacement=1) + EXIT + EXIT
        candidate = instruction(0x15, displacement=0) + EXIT + EXIT
        _graphs, report = models(original, candidate)
        self.assertTrue(any(row['kind'] == 'branch_target'
                            and row['classification'] == 'structural' for row in report['ranked']))

    def test_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, candidate = root / 'original.so', root / 'candidate.so'
            original.write_bytes(elf_fixture(instruction(0xb7, 1) + EXIT))
            candidate.write_bytes(elf_fixture(instruction(0xb7, 2) + EXIT))
            command = [sys.executable, '-B', str(Path(__file__).with_name('residual_analysis.py')),
                       str(original), str(candidate), '--original-window', '0x1000:16',
                       '--candidate-window', '0x1000:16', '--format', 'json']
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first.stderr, '')
            self.assertEqual(json.loads(first.stdout)['residuals']['by_kind'], {'register_usage': 1})


class CapturedWindowIntegrationTests(unittest.TestCase):
    def test_linked_symbol_changes_are_visible_despite_equal_call_bytes(self):
        root = Path(__file__).resolve().parents[2]
        original_path = root / 'evidence/original/pump/deployed.so'
        source = original_path.read_bytes()
        window = next(row for row in score.original_windows() if row['start'] == 0x22a10)
        original = residual.load_image_bytes(source, 'original', original_path)
        ow = residual.select_window(original, exact_window=(window['start'], window['bytes']))
        om = residual.build_function_model(original, ow)
        symbol = next(call['relocated_symbol'] for call in om['call_sequence'] if call.get('relocated_symbol'))
        changed = bytearray(captured_symbol_fixture(source, window['start'], window['bytes'], 'selected'))
        elf = residual.ELFFile(residual.BytesIO(changed))
        rel = elf.get_section_by_name('.rel.dyn')
        symbols = elf.get_section(rel['sh_link'])
        strings = elf.get_section(symbols['sh_link'])
        selected = next(item for item in symbols.iter_symbols() if item.name == symbol)
        at = strings['sh_offset'] + selected['st_name']
        changed[at] = ord('x') if changed[at] != ord('x') else ord('y')
        candidate = residual.load_image_bytes(bytes(changed), 'candidate', Path('changed.so'))
        cw = residual.select_window(candidate, exact_window=(window['start'], window['bytes']))
        self.assertEqual(ow['raw'], cw['raw'])
        cm = residual.build_function_model(candidate, cw)
        self.assertTrue(any(row['kind'] == 'call_target' for row in residual.compare_calls(om, cm)))
        self.assertEqual(original_path.read_bytes(), source)

    def test_relocated_call_cannot_enter_an_lddw_continuation(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'evidence/original/pump/deployed.so').read_bytes()
        changed = bytearray(source)
        elf = residual.ELFFile(residual.BytesIO(changed))
        text, rel = elf.get_section_by_name('.text'), elf.get_section_by_name('.rel.dyn')
        code = source[text['sh_offset']:text['sh_offset'] + text['sh_size']]
        offset = next(row['offset'] for row in residual.decode_instructions(code) if row['opcode'] == 0x18)
        entry = next(i for i, row in enumerate(rel.iter_relocations()) if row['r_info_type'] == 10)
        struct.pack_into('<Q', changed, rel['sh_offset'] + entry * 16, text['sh_addr'] + offset + 8)
        with self.assertRaisesRegex(ValueError, 'logical call instruction'):
            residual.load_image_bytes(bytes(changed), 'original', Path('bad-relocation.so'))

    def test_admin_cto_capture_round_trips_as_exact_window(self):
        root = Path(__file__).resolve().parents[2]
        original_path = root / 'evidence/original/pump/deployed.so'
        original_blob = original_path.read_bytes()
        window = next(row for row in score.original_windows() if row['start'] == 0x22a10)
        candidate_blob = captured_symbol_fixture(original_blob, window['start'], window['bytes'],
                                                 'captured_admin_cto')
        original = residual.load_image_bytes(original_blob, 'original', original_path)
        candidate = residual.load_image_bytes(candidate_blob, 'candidate', Path('captured-symbols.so'))
        ow = residual.select_window(original, exact_window=(window['start'], window['bytes']))
        cw = residual.select_window(candidate, exact_window=(window['start'], window['bytes']))
        om, cm = residual.build_function_model(original, ow), residual.build_function_model(candidate, cw)
        graphs = residual.compare_graphs(om, cm)
        report = residual.classify_residuals(om, cm, graphs['_mapping'])
        self.assertEqual((len(om['instructions']), len(cm['instructions'])),
                         (len(cm['instructions']), len(om['instructions'])))
        self.assertLess(len(om['instructions']), window['bytes'] // 8)  # retained LDDW coverage
        self.assertEqual(report['count'], 0)
        self.assertEqual(graphs['matching_summary']['unmatched_original'], 0)
        self.assertEqual(graphs['matching_summary']['unmatched_candidate'], 0)
        self.assertEqual(original_path.read_bytes(), original_blob)


if __name__ == '__main__':
    unittest.main()
