"""Unmodified full social-create corpus and bounded real-VM publication controls."""
import hashlib
import shutil
import unittest
from unittest.mock import patch
import publication_cli_support as support
from publication_cli_support import PublicationCase, ROOT

# main constructs its case list locally. Expose that exact construction only
# in the bounded child interpreter, without modifying files or any VM result.
# Full mode executes the original production main and all 588 cases.
ADAPTER = r'''
if mode!='full':
 import ast,copy
 tree=ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 def assigns(node,name):return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)
 start=next(i for i,n in enumerate(main.body) if assigns(n,'cases'))
 end=next(i for i,n in enumerate(main.body[start:],start) if assigns(n,'rows'))
 factory=ast.FunctionDef(name='cases',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(main.body[start:end])+[ast.Return(value=ast.Name(id='cases',ctx=ast.Load()))],decorator_list=[])
 main.body[start:end]=ast.parse("cases = globals()['cases']()").body
 exec(compile(ast.fix_missing_locations(ast.Module(body=[factory,main],type_ignores=[])),module.__file__,'exec'),module.__dict__)
'''


class FeesSocialCreateReportPublicationTests(PublicationCase, unittest.TestCase):
    NAMES=('fees_social_create_differential',)
    DATA=('evidence/upstream/pump_fees.json','evidence/original/pump_fees/deployed.so')
    HELPERS=('fees_admin_differential',)
    PROGRAM='evidence/original/pump_fees/deployed.so'
    EXPECTED={'fees_social_create_differential':588}

    def invoke(self,name,mode='bounded',output=None):
        needle='module=importlib.import_module(name)'
        self.assertIn(needle,support.DRIVER)
        driver=support.DRIVER.replace(needle,needle+'\n'+ADAPTER)
        with patch.object(support,'DRIVER',driver):
            return super().invoke(name,mode,output)

    def test_wrong_real_image_preserves_failed_report(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so',self.root/'candidate.so')
        result=self.invoke(self.NAMES[0])
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=self.report();self.assertEqual(len(report['cases']),2)
        self.assertTrue(report['mismatches'])
        self.assertEqual(report['candidate_sha256'],hashlib.sha256((self.root/'candidate.so').read_bytes()).hexdigest())


if __name__=='__main__':unittest.main()
