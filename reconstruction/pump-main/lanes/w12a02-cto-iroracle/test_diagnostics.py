from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import ctoracle  # noqa: E402
import iredit  # noqa: E402
class AdmissionTests(unittest.TestCase):
    def test_ranker_failure_is_not_success(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/pfboard.py'),'missing-candidate.so'],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('error',result.stdout)
    def test_empty_ranker_is_usage_error(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/pfboard.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
    def test_segment_size_is_checked_before_candidate_read(self):
        for value in ['0','-1']:
            result=subprocess.run([sys.executable,str(ROOT/'scripts/regionmap.py'),'missing-candidate.so',value],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('segment size must be positive',result.stderr)
class FnBoundsTests(unittest.TestCase):
    """Oracle edits must slice sym's defining `define`, wherever its first call site sits."""
    SYM='_ZN14pump_recovered9admin_cto7execute17h1638ff339e793c173E'
    CALLER_EQUIV='\n'.join([
        'define i32 @caller() #0 {',
        'entry:',
        f'  %r = call i32 @{SYM}(ptr null)',
        '  ret i32 %r',
        '}',
        '',
        f'define i32 @{SYM}(ptr %0) #0 {{',
        'entry:',
        '  %x = alloca [8 x i8], align 8',
        '  ret i32 0',
        '}',
        '',
        '@cte = internal constant { i32 } { i32 1 }',
        'define i32 @late_caller() #0 {',
        'entry:',
        f'  %r = call i32 @{SYM}(ptr null)',
        '  ret i32 %r',
        '}',
        '',
    ])
    def test_slices_the_definition_not_an_earlier_call(self):
        mod=self.CALLER_EQUIV
        start=mod.index(f'define i32 @{self.SYM}')
        i,j=ctoracle.fn_bounds(mod,self.SYM)
        self.assertEqual((i,j),(start,mod.index('\n}\n',start)+3))
        self.assertNotIn('@caller',mod[i:j])
    def test_definition_first_module_keeps_its_bounds(self):
        mod='\n'.join([
            f'define i32 @{self.SYM}() #0 {{',
            'entry:',
            '  ret i32 0',
            '}',
            '',
            'define i32 @caller() #0 {',
            'entry:',
            f'  %r = call i32 @{self.SYM}()',
            '  ret i32 %r',
            '}',
            '',
        ])
        start=0
        i,j=ctoracle.fn_bounds(mod,self.SYM)
        self.assertEqual((i,j),(start,mod.index('\n}\n',start)+3))
    def test_missing_definition_is_refused(self):
        declare=f'declare i32 @{self.SYM}(ptr)\n'
        with self.assertRaises(ValueError) as ctx:
            ctoracle.fn_bounds(declare,self.SYM)
        self.assertIn('no definition of',str(ctx.exception))
    def test_iredit_split_fn_slices_the_definition(self):
        pre,fn,post=iredit.split_fn(self.CALLER_EQUIV)
        self.assertIn(f'define i32 @{self.SYM}',fn)
        self.assertNotIn('@caller',fn)
        self.assertEqual(pre+fn+post,self.CALLER_EQUIV)
if __name__=='__main__':unittest.main()
