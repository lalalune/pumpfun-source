"""Synthetic correctness tests for conservative SBPF register/stack provenance."""
import struct
import unittest
from pathlib import Path

import sbpf_provenance as provenance
import stack_access


def instruction(opcode, dst=0, src=0, displacement=0, immediate=0):
    return struct.pack('<BBhi', opcode, dst | (src << 4), displacement, immediate)


def lddw(dst, value):
    low = value & 0xffffffff
    low = low - (1 << 32) if low >= 1 << 31 else low
    return (instruction(0x18, dst=dst, immediate=low)
            + bytes(4) + struct.pack('<I', value >> 32))


EXIT = instruction(0x95)


class RegisterAndAliasTests(unittest.TestCase):
    def test_mov_chain_and_r10_arithmetic_prove_derived_access(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x07, 1, immediate=-32),
            instruction(0xbf, 2, 1), instruction(0x79, 3, 2, -8), EXIT,
        ])
        report = provenance.analyze(raw)
        access = report['stack_accesses']['proven'][0]
        self.assertEqual((access['stack_offset'], access['width'], access['alias_kind']),
                         (-40, 8, 'derived'))
        self.assertEqual([row['register'] for row in report['stack_pointer_aliases']], [1, 1, 2])
        self.assertIn(0, access['reaching_definition_evidence']['reaching_definitions'])
        self.assertIn(8, access['reaching_definition_evidence']['reaching_definitions'])

    def test_direct_r10_access_remains_distinct(self):
        report = provenance.analyze(instruction(0x61, 1, 10, -12) + EXIT)
        access = report['stack_accesses']['proven'][0]
        self.assertEqual((access['stack_offset'], access['width'], access['alias_kind']),
                         (-12, 4, 'direct'))

    def test_lddw_and_constant_arithmetic_propagate(self):
        value = 0x1234567887654321
        report = provenance.analyze(lddw(1, value) + instruction(0x07, 1, immediate=3) + EXIT)
        exit_fact = report['register_states'][0]['exit_known_registers']['1']
        self.assertEqual(exit_fact['kind'], 'constant')
        self.assertEqual(exit_fact['value'], (value + 3) & ((1 << 64) - 1))

    def test_same_stack_alias_survives_cfg_join_with_ambiguity(self):
        raw = b''.join([
            instruction(0x15, 0, displacement=2),
            instruction(0xbf, 1, 10), instruction(0x05, displacement=1),
            instruction(0xbf, 1, 10), instruction(0x79, 2, 1, -8), EXIT,
        ])
        report = provenance.analyze(raw)
        access = report['stack_accesses']['proven'][0]
        self.assertTrue(access['reaching_definition_evidence']['path_ambiguous'])
        self.assertEqual(access['stack_offset'], -8)

    def test_conflicting_stack_alias_join_is_potential_never_proven(self):
        raw = b''.join([
            instruction(0x15, 0, displacement=3),
            instruction(0xbf, 1, 10), instruction(0x07, 1, immediate=-8),
            instruction(0x05, displacement=2),
            instruction(0xbf, 1, 10), instruction(0x07, 1, immediate=-16),
            instruction(0x79, 2, 1), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(report['stack_accesses']['proven'], [])
        self.assertEqual(report['stack_accesses']['potential'][0]['candidate_stack_offsets'], [-16, -8])

    def test_known_branch_prunes_infeasible_alias_definition(self):
        raw = b''.join([
            instruction(0xb7, 0, immediate=1), instruction(0x15, 0, displacement=2, immediate=1),
            instruction(0xbf, 1, 10), instruction(0x05, displacement=1),
            instruction(0xbf, 1, 10), instruction(0x79, 2, 1, -8), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(report['stack_accesses']['proven'][0]['stack_offset'], -8)
        self.assertTrue(any(row['constant_pruned_successors'] for row in report['register_states']))

    def test_loop_converges_without_inventing_aliases(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x15, 0, displacement=1),
            instruction(0x05, displacement=-2), instruction(0x79, 2, 1, -8), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertLess(report['fixed_point_steps'], 20)
        self.assertEqual(report['stack_accesses']['proven'][0]['stack_offset'], -8)


class MemoryAndCallTests(unittest.TestCase):
    def test_pointer_spill_and_reload_recovers_stack_alias(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x07, 1, immediate=-64),
            instruction(0x7b, 10, 1, -8), instruction(0x79, 2, 10, -8),
            instruction(0x79, 3, 2, 4), EXIT,
        ])
        report = provenance.analyze(raw)
        reads = [row for row in report['stack_accesses']['proven'] if row['kind'] == 'read']
        self.assertTrue(reads[0]['recovered_stack_pointer'])
        self.assertEqual(reads[1]['stack_offset'], -60)
        self.assertEqual(len(report['suspected_spill_reload_patterns']), 1)

    def test_overlapping_store_invalidates_pointer_spill(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x7b, 10, 1, -8),
            instruction(0x63, 10, 0, -4), instruction(0x79, 2, 10, -8),
            instruction(0x79, 3, 2), EXIT,
        ])
        report = provenance.analyze(raw)
        last = report['stack_accesses']['unknown'][-1]
        self.assertEqual(last['base_register'], 2)
        self.assertFalse(any(row.get('recovered_stack_pointer') for row in report['stack_accesses']['proven']))

    def test_call_clobbers_argument_register_and_records_escape(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x07, 1, immediate=-32),
            instruction(0x85), instruction(0x79, 2, 1), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(len(report['pointer_escapes']), 1)
        self.assertEqual(report['stack_accesses']['unknown'][0]['base_register'], 1)

    def test_callee_saved_register_preserves_stack_alias(self):
        raw = b''.join([
            instruction(0xbf, 6, 10), instruction(0x07, 6, immediate=-48),
            instruction(0x85), instruction(0x79, 1, 6), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(report['stack_accesses']['proven'][0]['stack_offset'], -48)

    def test_indirect_call_uses_same_clobber_and_escape_rule(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x8d, immediate=6),
            instruction(0x79, 2, 1), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(report['pointer_escapes'][0]['call_kind'], 'indirect')
        self.assertEqual(len(report['stack_accesses']['unknown']), 1)

    def test_unknown_store_clears_tracked_memory(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x7b, 10, 1, -8),
            instruction(0x7b, 2, 1), instruction(0x79, 3, 10, -8), EXIT,
        ])
        report = provenance.analyze(raw)
        reload = [row for row in report['stack_accesses']['proven']
                  if row['kind'] == 'read'][0]
        self.assertNotIn('recovered_stack_pointer', reload)


class UnknownAndLivenessTests(unittest.TestCase):
    def test_unsupported_opcode_kills_alias_and_is_reported(self):
        raw = b''.join([
            instruction(0xbf, 1, 10), instruction(0x00, 1),
            instruction(0x79, 2, 1), EXIT,
        ])
        report = provenance.analyze(raw)
        self.assertEqual(len(report['stack_accesses']['unknown']), 1)
        self.assertTrue(any(row['kind'] == 'unsupported_opcode' for row in report['diagnostics']))

    def test_truncated_lddw_and_empty_stream_are_rejected(self):
        for raw in (b'', instruction(0x18)):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                provenance.analyze(raw)

    def test_liveness_reports_live_sets_pressure_and_dead_definitions(self):
        raw = b''.join([
            instruction(0xb7, 1, immediate=7), instruction(0xbf, 2, 1),
            instruction(0xb7, 3, immediate=9), instruction(0xbf, 0, 2), EXIT,
        ])
        report = provenance.analyze(raw)
        live = report['liveness']
        self.assertGreaterEqual(live['maximum_register_pressure'], 1)
        self.assertTrue(any(row['register'] == 3 for row in live['dead_definitions']))

    def test_unknown_pointer_is_never_silently_stack_relative(self):
        report = provenance.analyze(instruction(0x79, 1, 2, -8) + EXIT)
        self.assertEqual(report['stack_accesses']['proven'], [])
        self.assertEqual(report['stack_accesses']['potential'], [])
        self.assertEqual(len(report['stack_accesses']['unknown']), 1)


class CapturedAdminCtoTests(unittest.TestCase):
    def test_proven_direct_inventory_exactly_preserves_maintained_tool(self):
        root = Path(__file__).resolve().parents[2]
        raw, identity = stack_access.read_range(
            root / 'evidence/original/pump/deployed.so', 0x22a10, 27_400)
        legacy = stack_access.accesses(raw)['accesses']
        report = provenance.analyze(raw, 0x22a10)
        proven = [row for row in report['stack_accesses']['proven']
                  if row['alias_kind'] == 'direct']
        self.assertEqual(identity['sha256'],
                         '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d')
        self.assertEqual(
            [(row['instruction_offset'], row['offset'], row['width'], row['kind']) for row in legacy],
            [(row['instruction_offset'], row['stack_offset'], row['width'], row['kind']) for row in proven])
        self.assertGreater(len(report['stack_pointer_aliases']), 400)
        self.assertGreater(len(report['pointer_escapes']), 100)
        self.assertGreater(len(report['suspected_spill_reload_patterns']), 20)


class WidthAndAliasRegressionTests(unittest.TestCase):
    def test_partial_pointer_spills_do_not_recover_a_whole_stack_pointer(self):
        for store, load in ((0x73, 0x71), (0x6b, 0x69), (0x63, 0x61)):
            raw = (instruction(0xbf, 1, 10) + instruction(store, 10, 1, -8)
                   + instruction(load, 2, 10, -8) + instruction(0x79, 3, 2) + EXIT)
            with self.subTest(store=store):
                report = provenance.analyze(raw)
                self.assertFalse(any(row['base_register'] == 2 for row in report['stack_accesses']['proven']))
                self.assertEqual(report['stack_accesses']['unknown'][-1]['base_register'], 2)
                self.assertFalse(any(row.get('recovered_stack_pointer')
                                     for row in report['stack_accesses']['proven']))

    def test_narrow_constant_stores_retain_only_the_written_low_bytes(self):
        for width, store, load in ((1, 0x73, 0x71), (2, 0x6b, 0x69), (4, 0x63, 0x61)):
            raw = (lddw(1, (1 << (width * 8)) + 7) + instruction(store, 10, 1, -8)
                   + instruction(load, 2, 10, -8) + EXIT)
            with self.subTest(width=width):
                report = provenance.analyze(raw)
                self.assertEqual(report['register_states'][0]['exit_known_registers']['2']['value'], 7)

    def test_mov32_negative_immediate_is_zero_extended(self):
        report = provenance.analyze(instruction(0xb4, 1, immediate=-1) + EXIT)
        self.assertEqual(report['register_states'][0]['exit_known_registers']['1']['value'], 0xffffffff)

    def test_legacy_register_shifts_mask_the_shift_count(self):
        # solana-sbpf v0.12.2 interpreter uses wrapping_shl/wrapping_shr
        # for both legacy widths; ARSH first casts to the signed width.
        for bits, shift in ((32, 0x6c), (64, 0x6f), (32, 0x7c), (64, 0x7f),
                            (32, 0xcc), (64, 0xcf)):
            raw = (instruction(0xb7, 1, immediate=8) + instruction(0xb7, 2, immediate=bits)
                   + instruction(shift, 1, 2) + EXIT)
            with self.subTest(bits=bits, shift=shift):
                report = provenance.analyze(raw)
                self.assertEqual(report['register_states'][0]['exit_known_registers']['1']['value'], 8)

    def test_unknown_call_arguments_do_not_preserve_tracked_frame_memory(self):
        raw = (instruction(0xbf, 6, 10) + instruction(0x7b, 10, 6, -8)
               + instruction(0x85) + instruction(0x79, 2, 10, -8)
               + instruction(0x79, 3, 2) + EXIT)
        report = provenance.analyze(raw)
        self.assertFalse(any(row['base_register'] == 2 for row in report['stack_accesses']['proven']))
        self.assertEqual(report['stack_accesses']['unknown'][-1]['base_register'], 2)
        self.assertFalse(any(row.get('recovered_stack_pointer')
                             for row in report['stack_accesses']['proven']))

    def test_stack_pointer_addition_obeys_modulo_64_bit_arithmetic(self):
        raw = (instruction(0xbf, 1, 10) + lddw(2, 1 << 63)
               + instruction(0x0f, 1, 2) + instruction(0x0f, 1, 2)
               + instruction(0x79, 3, 1, -8) + EXIT)
        report = provenance.analyze(raw)
        self.assertEqual(report['stack_accesses']['proven'][0]['stack_offset'], -8)


if __name__ == '__main__':
    unittest.main()
