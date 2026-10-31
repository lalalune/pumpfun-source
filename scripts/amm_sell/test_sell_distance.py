"""Exact instruction edit-distance regressions; no compiler or VM required."""
import importlib.util
import itertools
import hashlib
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('distance_sell_score', HERE / 'sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


def tokens(values):
    # Complete, valid mov64-immediate instructions. Constants are preserved by
    # the real listing and token normalization, not supplied as fake token rows.
    raw = b''.join(struct.pack('<BBhi', 0xb7, 0, 0, value) for value in values)
    image = type('Image', (), {'b': raw})()
    return score.normalized_tokens(score.listing(image, 0, len(raw)))


class AlignmentDistanceTests(unittest.TestCase):
    def test_captured_amm_indirect_calls_keep_their_register_form(self):
        path = HERE.parents[1] / 'evidence/original/pump_amm/deployed.so'
        image = score.elf_reader.Elf(path)
        self.assertEqual(hashlib.sha256(image.b).hexdigest(), score.ORIGINAL_SHA)
        self.assertEqual(struct.unpack_from('<I', image.b, 48)[0], 0)
        rows = score.listing(image, image.lo, image.hi - image.lo)
        indirect = [row for row in rows if bytes.fromhex(row['raw'])[0] == 0x8d]
        self.assertEqual(len(indirect), 123)
        for row in indirect:
            register = struct.unpack_from('<i', bytes.fromhex(row['raw']), 4)[0]
            self.assertEqual(row['text'], f'callx r{register}')
            self.assertEqual(row['fields'], ('callx', register))
            self.assertIsNone(row['target'])
        self.assertEqual(path.read_bytes(), image.b)

    def test_indirect_call_does_not_collide_with_immediate_call(self):
        # V0 CALL_REG selects a register through imm, while CALL_IMM uses a
        # literal callee key. These eight-byte instructions used to tokenize
        # identically despite differing in the opcode that selects that meaning.
        def instruction(opcode):
            raw = struct.pack('<BBhi', opcode, 0, 0, 2)
            return score.normalized_tokens(score.listing(SimpleNamespace(b=raw), 0, 8))
        immediate, indirect = instruction(0x85), instruction(0x8d)
        self.assertNotEqual(immediate, indirect)
        self.assertEqual(score.alignment_distance(immediate, indirect), 1)

    def test_indirect_register_identity_and_immediate_call_controls(self):
        def row(opcode, regs, immediate, start=0):
            raw = bytes(start) + struct.pack('<BBhi', opcode, regs, 0, immediate)
            return score.listing(SimpleNamespace(b=raw), start, 8)[0]
        left, right = row(0x8d, 0, 2), row(0x8d, 0, 3)
        self.assertEqual(score.alignment_distance(score.normalized_tokens([left]),
                                                 score.normalized_tokens([right])), 1)
        self.assertEqual(score.normalized_tokens([left]),
                         score.normalized_tokens([row(0x8d, 0, 2, start=64)]))
        internal, syscall = row(0x85, 0x10, -2, start=64), row(0x85, 0, 2)
        self.assertEqual(internal['fields'], ('call', 1, -2))
        self.assertEqual(internal['target'], ('call', 56))
        self.assertEqual(syscall['fields'], ('call', 0, 2))
        self.assertIsNone(syscall['target'])
        self.assertEqual(score.normalized_tokens([internal, syscall]),
                         ['call 0x38', 'call 0 2'])

    def test_distance_matches_full_grid_for_repeated_short_sequences(self):
        # Independent full matrix oracle, including empty sequences, repeated
        # boundary values, asymmetric insertions and competing alignments.
        sequences = [values for size in range(5)
                     for values in itertools.product(range(3), repeat=size)]
        for left in sequences:
            for right in sequences:
                grid = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
                for i in range(len(left) + 1):
                    grid[i][0] = i
                for j in range(len(right) + 1):
                    grid[0][j] = j
                for i, a in enumerate(left, 1):
                    for j, b in enumerate(right, 1):
                        grid[i][j] = min(grid[i-1][j] + 1, grid[i][j-1] + 1,
                                         grid[i-1][j-1] + (a != b))
                self.assertEqual(score.alignment_distance(left, right), grid[-1][-1],
                                 (left, right))

    def test_one_substitution_between_repeated_instructions_costs_one(self):
        self.assertEqual(score.alignment_distance(tokens([0, 0, 0]), tokens([0, 1, 0])), 1)
        self.assertEqual(score.alignment_distance(tokens([0, 1, 0]), tokens([0, 0, 0])), 1)

    def test_two_substitutions_beat_a_longer_matching_block_alignment(self):
        self.assertEqual(score.alignment_distance(tokens([0, 0, 0, 0]), tokens([0, 1, 1, 0])), 2)

    def test_empty_identical_and_indel_controls(self):
        a = tokens([0, 1, 2])
        for left, right, expected in (([], [], 0), (a, [], 3), ([], a, 3),
                                      (a, a, 0), (a, tokens([0, 2]), 1),
                                      (tokens([0, 2]), a, 1), (a, tokens([3, 4, 5]), 3)):
            with self.subTest(left=left, right=right):
                self.assertEqual(score.alignment_distance(left, right), expected)

    def test_absent_candidate_tail_counts_as_differing_slots(self):
        # A candidate shorter than the sell window used to shrink the slice
        # and publish slot_diffs: 0 for a window that is simply missing.
        original = bytes(range(8)) * 3                      # three full slots
        same = score.slot_differences(original, original)
        one_changed = score.slot_differences(original, bytes(8) + original[8:])
        truncated = score.slot_differences(original, original[:20])   # last slot absent
        missing = score.slot_differences(original, b'')               # whole window absent
        self.assertEqual(same, 0)
        self.assertEqual(one_changed, 1)
        self.assertEqual(truncated, 1)
        self.assertEqual(missing, 3)


    def test_endian_forms_preserve_direction_and_width(self):
        for opcode, direction in ((0xd4, 'le'), (0xdc, 'be')):
            for width in (16, 32, 64):
                with self.subTest(opcode=hex(opcode), width=width):
                    raw = struct.pack('<BBhi', opcode, 5, 0, width)
                    rows = list(score.decode(raw, 0, len(raw)))
                    self.assertEqual(len(rows), 1)
                    offset, size, decoded, text, fields = rows[0]
                    self.assertEqual((offset, size, decoded), (0, 8, raw))
                    self.assertEqual(text, f'{direction}{width} r5')
                    # END's immediate is the width, not a register operand.
                    self.assertEqual(fields, (direction, 5, None, width))

    def test_endian_tokens_distinguish_width_and_direction(self):
        tokens = []
        for opcode, direction in ((0xd4, 'le'), (0xdc, 'be')):
            for width in (16, 32, 64):
                raw = struct.pack('<BBhi', opcode, 5, 0, width)
                rows = score.listing(SimpleNamespace(b=raw), 0, len(raw))
                self.assertEqual(rows[0]['raw'], raw.hex())
                self.assertIsNone(rows[0]['target'])
                self.assertEqual(score.normalized_tokens(rows),
                                 [f'{direction} 5 None {width}'])
                tokens.extend(score.normalized_tokens(rows))
        self.assertEqual(len(set(tokens)), 6)

    def test_endian_decode_preserves_other_alu_operand_forms(self):
        for opcode, regs, immediate, text, fields in (
            (0x04, 5, 16, 'add32 r5, 16', ('add32', 5, None, 16)),
            (0x0c, 0x35, 0, 'add32 r5, r3', ('add32', 5, 3, None)),
            (0xb7, 5, 64, 'mov r5, 64', ('mov', 5, None, 64)),
            (0xbf, 0x35, 0, 'mov r5, r3', ('mov', 5, 3, None)),
        ):
            with self.subTest(opcode=hex(opcode)):
                raw = struct.pack('<BBhi', opcode, regs, 0, immediate)
                self.assertEqual(list(score.decode(raw, 0, len(raw)))[0],
                                 (0, 8, raw, text, fields))


if __name__ == '__main__':
    unittest.main()
