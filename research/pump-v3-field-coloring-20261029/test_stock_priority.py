"""Mutation controls for replacing the private field patch with a stock option."""
from pathlib import Path
import copy,importlib.util,unittest
P=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('stock_priority_checks',P/'verify_stock_priority.py')
parent=load('stock_priority_parent',P.parent/'pump-v3-regalloc-20261029/verify.py')
class StockPriorityControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=v.text('stock-priority/frequency-reverse1-scheduler1/stderr.log')
        cls.before=parent.data('costs/ir01/frequency/input.ll');cls.after=v.data('stock-priority/stores-frequency.ll')
        cls.launch=v.record('stock-priority/frequency-reverse1-scheduler0/launch.json')
        cls.base=parent.record('costs/ir01/frequency/launch.json')
        cls.flags=cls.launch['command'][11:];cls.tool=cls.launch['tool_sha256']
    def test_recorded_allocation_and_formula(self):
        row=v.allocation(self.t,True)
        self.assertEqual(row['derived_reverse_priorities'],{'101':2147485248,'100':2147485244})
    def test_wrong_endpoint(self):
        with self.assertRaisesRegex(ValueError,'endpoints'):v.allocation(self.t.replace('[6368r,6400r:0)','[6368r,6401r:0)'),True)
    def test_order_is_not_forward_priority(self):
        with self.assertRaisesRegex(ValueError,'endpoints'):v.allocation(self.t,False)
    def test_wrong_field_color(self):
        with self.assertRaisesRegex(ValueError,'field colors'):v.allocation(self.t.replace('assigning %101 to $r1:','assigning %101 to $r2:'),True)
    def test_private_patch_cannot_hide_in_trace(self):
        with self.assertRaisesRegex(ValueError,'private field'):v.allocation(self.t+'\nV3_FIELD_COUNTERFACTUAL unexpected\n',True)
    def test_recorded_store_delta(self):v.input_delta(self.before,self.after)
    def test_extra_store_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'disjoint result stores'):v.input_delta(self.before,self.after.replace(b'store ptr %_84.1, ptr %50, align 8',b'store ptr %_84.1, ptr %49, align 8'))
    def test_extra_private_flag_is_rejected(self):
        v.command_check(self.launch,self.base,self.flags,self.tool,self.before)
        changed=copy.deepcopy(self.launch);changed['command'].append('-v3-diagnostic-field-priority')
        with self.assertRaisesRegex(ValueError,'literal supported-option'):v.command_check(changed,self.base,self.flags,self.tool,self.before)
    def test_compiler_and_input_are_bound(self):
        for key in ['tool_sha256','input_sha256']:
            changed=copy.deepcopy(self.launch);changed[key]='0'*64
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'compiler/input'):v.command_check(changed,self.base,self.flags,self.tool,self.before)
if __name__=='__main__':unittest.main()
