#!/usr/bin/env python3
"""Event normalization never pads truncated input, including optimized execution."""
import ast
from pathlib import Path
import unittest

SCRIPTS=Path(__file__).resolve().parent
DRIVERS=('pump_migrate_surfpool.py','pump_holder_distribution_surfpool.py',
         'pump_exact_quote_surfpool.py','pump_v3_configured_fee_surfpool.py')
def load_normalize_event(name,optimize):
    tree=ast.parse((SCRIPTS/name).read_text(encoding='utf-8'))
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_event')
    namespace={}
    exec(compile(ast.Module(body=[function],type_ignores=[]),name,'exec',optimize=optimize),namespace)
    return namespace['normalize_event']

class TruncatedEventNormalizationTests(unittest.TestCase):
    KEY=b'\x01'*8
    def test_full_event_only_zeroes_the_timestamp(self):
        for name in DRIVERS:
            for optimize in (0,1,2):
                with self.subTest(driver=name,optimize=optimize):
                    data=self.KEY+b'\x02'*24
                    out=load_normalize_event(name,optimize)(data,{self.KEY:16})
                    self.assertEqual(out,data[:16]+bytes(8)+data[24:])
                    self.assertEqual(len(out),len(data))
    def test_truncated_events_fail_in_every_optimization_mode(self):
        for name in DRIVERS:
            for optimize in (0,1,2):
                for length in (8,15,16,20,23):
                    with self.subTest(driver=name,optimize=optimize,length=length):
                        data=self.KEY+b'\x02'*(length-8)
                        with self.assertRaisesRegex(ValueError,'truncated event'):
                            load_normalize_event(name,optimize)(data,{self.KEY:16})
    def test_unknown_event_fails_in_every_optimization_mode(self):
        for name in DRIVERS:
            for optimize in (0,1,2):
                with self.subTest(driver=name,optimize=optimize):
                    with self.assertRaisesRegex(ValueError,'unknown event'):
                        load_normalize_event(name,optimize)(b'wrong',{})

if __name__=='__main__':unittest.main()
