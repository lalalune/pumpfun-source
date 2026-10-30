"""Direct validators retain the exact input tuples of the arithmetic producer."""
import ast
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pump_constant_product_cases import input_cases

class ConstantProductInputCasesTests(unittest.TestCase):
    def test_matches_current_producer_loop_without_importing_execution_results(self):
        tree=ast.parse((ROOT/'scripts/pump_validate_constant_product.py').read_text(encoding='utf-8'))
        assignments=[]
        loop=None
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('rng','amounts','states') for t in node.targets):
                assignments.append(node)
            if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple) and [getattr(t,'id',None) for t in node.target.elts]==['vi','vq']:
                loop=node
        self.assertEqual(len(assignments),3)
        self.assertIsNotNone(loop)
        inner=loop.body[0]
        self.assertIsInstance(inner,ast.For)
        self.assertEqual(inner.target.id,'amount')
        collect=ast.parse("rows.append({'amount_in': amount, 'reserve_in': vi, 'reserve_out': vq})").body
        inner=ast.For(target=inner.target,iter=inner.iter,body=collect,orelse=[])
        outer=ast.For(target=loop.target,iter=loop.iter,body=[inner],orelse=[])
        module=ast.fix_missing_locations(ast.Module(body=[*assignments,outer],type_ignores=[]))
        for base,quote in ((1073000000,30000000000),(1,100),(987654321,123456789)):
            with self.subTest(base=base,quote=quote):
                namespace={'random':random,'base':base,'quote':quote,'rows':[]}
                exec(compile(module,'producer-inputs','exec'),namespace)
                self.assertEqual(input_cases(base,quote),namespace['rows'])

if __name__=='__main__':unittest.main()
