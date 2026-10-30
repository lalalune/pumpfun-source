import struct
import unittest
from control_flow import cycle_regions
from control_flow import analyze


def graph(edges):
    return [{'offset': i, 'reachable': True, 'successors': [dict(target=j, internal=True) for j in targets]}
            for i, targets in enumerate(edges)]


class CycleRegionTests(unittest.TestCase):
    def test_self_loop_and_entry(self):
        self.assertEqual(cycle_regions(graph([[0]])), [dict(blocks=[0], reachable=True, entry_blocks=[0])])

    def test_nested_cycles_form_one_region(self):
        r = cycle_regions(graph([[1], [2], [1, 3], [2, 4], []]))
        self.assertEqual(r, [dict(blocks=[1, 2, 3], reachable=True, entry_blocks=[1])])

    def test_multiple_entries(self):
        self.assertEqual(cycle_regions(graph([[1, 2], [2], [1]]))[0]['entry_blocks'], [1, 2])

    def test_unreachable_loop_from_decoder(self):
        raw = struct.pack('<BBhi', 0x95, 0, 0, 0) + struct.pack('<BBhi', 0x05, 0, -1, 0)
        self.assertEqual(analyze(raw)['cyclic_regions'], [dict(blocks=[8], reachable=False, entry_blocks=[])])

    def test_deep_acyclic_graph(self):
        self.assertEqual(cycle_regions(graph([[i+1] for i in range(5000)] + [[]])), [])

    def test_lddw_payload_is_not_loop(self):
        raw = struct.pack('<BBhi', 0x18, 0, 0, 0) + struct.pack('<BBhi', 0x05, 0, -1, 0)
        self.assertEqual(analyze(raw)['cyclic_regions'], [])
