"""Compare cross-section frequency output with an independent retained-ELF scan."""
from collections import Counter
import hashlib
from pathlib import Path
import struct
import unittest

from deep_section_analysis import analyze_cross_section
from window_elf_reader import Elf

ROOT=Path(__file__).resolve().parents[1]


class CrossSectionFrequency(unittest.TestCase):
    def test_fees_hot_addresses_count_all_references_before_display_truncation(self):
        elf=Elf(ROOT/'evidence/original/pump_fees/deployed.so')
        self.assertEqual(hashlib.sha256(elf.b).hexdigest(),'4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e')
        section=elf.secs['.rodata']
        expected=Counter()
        for start,end in zip(elf.entries,elf.entries[1:]+[elf.hi]):
            for at in range(start,end,8):
                if elf.b[at]==0x18 and at+16<=end:
                    low=struct.unpack_from('<I',elf.b,at+4)[0]
                    high=struct.unpack_from('<I',elf.b,at+12)[0]
                    address=low+(high<<32)
                    if section[4]<=address<section[4]+section[5]:expected[hex(address)]+=1
        report=analyze_cross_section(elf)
        self.assertEqual(sum(expected.values()),1548)
        self.assertEqual(report['total_rodata_refs'],1548)
        self.assertEqual(sum(len(w['rodata_addresses']) for w in report['window_data_refs']),1305)
        self.assertTrue(all(len(w['rodata_addresses'])<=20 for w in report['window_data_refs']))
        actual={row['address']:row['ref_count'] for row in report['hot_rodata_addresses']}
        self.assertEqual(actual,dict(expected.most_common(50)))
        for address,count in [('0xc4ead',84),('0xc4a24',42),('0xc4afc',38),('0xc4c1c',29)]:
            self.assertEqual(actual[address],count)

    def test_data_reference_aggregation_also_keeps_occurrences_beyond_twenty(self):
        # Reclassify the same complete, unchanged .rodata byte interval as the
        # data-rel-ro category for this consumer; no binary bytes are fabricated.
        elf=Elf(ROOT/'evidence/original/pump_fees/deployed.so')
        original=elf.secs.pop('.rodata')
        elf.secs['.data.rel.ro']=original
        report=analyze_cross_section(elf)
        actual={row['address']:row['ref_count'] for row in report['hot_data_rel_ro_addresses']}
        self.assertEqual(report['total_data_refs'],1548)
        self.assertEqual(actual['0xc4ead'],84)
        self.assertEqual(actual['0xc4c1c'],29)


if __name__=='__main__':unittest.main()
