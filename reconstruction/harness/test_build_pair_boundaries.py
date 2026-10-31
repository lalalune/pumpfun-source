import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_score_pair as P

class PairBoundaryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.base=self.root/'base';self.candidate=self.root/'candidate';self.sdk=self.root/'sdk';self.hybrid=self.root/'hybrid'
        for tool in [self.sdk/'llvm/bin/llvm-objdump',self.sdk/'llvm/bin/llvm-objcopy',
                     self.sdk/'llvm/bin/clang',self.sdk/'rust/bin/cargo',self.hybrid/'rust/bin/rustc']:
            tool.parent.mkdir(parents=True,exist_ok=True);tool.write_bytes(b'fixture tool')
        self.windows={0:{'bytes':8,'normalized':True,'raw':True}}
        self.state={'base':'before','candidate':'before'}
        self.config=(P.fastbuild.SDK,P.fastbuild.LOCKDIR,P.fastbuild.RECIPES['identity'],P.score.BASE,getattr(P.score,'OBJDUMP',None))
        self.addCleanup(self.restore)
    def restore(self):
        P.fastbuild.SDK,P.fastbuild.LOCKDIR,P.fastbuild.RECIPES['identity'],P.score.BASE,old_objdump=self.config
        if old_objdump is None:P.score.__dict__.pop('OBJDUMP',None)
        else:P.score.OBJDUMP=old_objdump
    def source(self,repo):return {'sha256':self.state[Path(repo).name]}
    def build(self,src,work,out,**kw):
        out.mkdir(parents=True);(out/'unstripped.so').write_bytes(b'fixture')
        return {'ok':True,'runtime_valid':True,'stack_warnings':[],
                'unstripped_sha256':hashlib.sha256(b'fixture').hexdigest()}
    def run_pair(self,name='out',**kw):return P.run_pair(self.base,self.candidate,self.root/name,self.sdk,self.hybrid,**kw)
    def patches(self,build=None):
        from contextlib import ExitStack
        s=ExitStack();s.enter_context(patch.object(P,'source_receipt',side_effect=self.source));s.enter_context(patch.object(P.fastbuild,'build',side_effect=build or self.build));s.enter_context(patch.object(P.score,'score',return_value=self.windows));return s
    def test_base_mutation_during_candidate_build_is_rejected(self):
        def build(src,*args,**kw):
            result=self.build(src,*args,**kw)
            if self.candidate in src.parents:self.state['base']='changed'
            return result
        with self.patches(build):
            with self.assertRaisesRegex(ValueError,'source changed'):self.run_pair()
        r=json.loads((self.root/'out/receipt.json').read_text());self.assertNotIn('comparison',r)
    def test_bound_tool_mutation_is_rejected(self):
        def build(src,*args,**kw):
            result=self.build(src,*args,**kw)
            if self.candidate in src.parents:(self.hybrid/'rust/bin/rustc').write_bytes(b'changed')
            return result
        with self.patches(build):
            with self.assertRaisesRegex(ValueError,'tool|input'):self.run_pair()
    def test_configuration_restored_after_success_failure_and_setup_failure(self):
        for kind in ['pass','fail','setup']:
            with self.subTest(kind=kind),self.patches():
                with patch.object(P,'require_valid_build',side_effect=ValueError('failed')) if kind=='fail' else patch.object(P,'copy_original_inputs',side_effect=ValueError('setup')) if kind=='setup' else patch.object(P,'require_valid_build'):
                    if kind=='pass':self.assertEqual(self.run_pair(kind),0)
                    else:
                        with self.assertRaises(ValueError):self.run_pair(kind)
                self.assertEqual((P.fastbuild.SDK,P.fastbuild.LOCKDIR,P.fastbuild.RECIPES['identity'],P.score.BASE,getattr(P.score,'OBJDUMP',None)),self.config)
    def test_deadline_is_forwarded_and_invalid_deadlines_do_not_create_output(self):
        with self.patches(),patch.object(P.fastbuild,'build',side_effect=self.build) as build:
            self.assertEqual(self.run_pair(timeout=.5),0)
            self.assertEqual([c.kwargs['timeout'] for c in build.call_args_list],[.5,.5])
        for timeout in [0,-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):self.run_pair('invalid',timeout=timeout)
            self.assertFalse((self.root/'invalid').exists())
if __name__=='__main__':unittest.main()
