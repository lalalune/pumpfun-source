import base64,hashlib,importlib.util,io,json,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('progress_regression',Path(__file__).resolve().parents[1]/'scripts/progress.py')
progress=importlib.util.module_from_spec(spec);spec.loader.exec_module(progress)
def fixture(root):
    for name in ['contracts','evidence/web/objects','evidence/sdk','recovered','packages/sdk/src']:(root/name).mkdir(parents=True,exist_ok=True)
    values={'contracts/feature-progress.json':{'asOf':'2026-10-29','frontend':[],'backend':[],'gates':{},'exclusions':[],'deferred':[]},'contracts/internal-operations.json':{'operations':[]},'contracts/developer.openapi.json':{'paths':{}},'recovered/modules.json':{'modules':[]},'evidence/web/manifest.json':{'records':[]}}
    for name,value in values.items():(root/name).write_text(json.dumps(value),encoding='utf-8')
    body=b'export {};';(root/'packages/sdk/src/index.ts').write_bytes(body)
    with tarfile.open(root/'evidence/sdk/pump-sdk-4.3.1.tgz','w:gz') as tar:
        member=tarfile.TarInfo('package/src/index.ts');member.size=len(body);tar.addfile(member,io.BytesIO(body))
    integrity='sha512-'+base64.b64encode(hashlib.sha512((root/'evidence/sdk/pump-sdk-4.3.1.tgz').read_bytes()).digest()).decode()
    (root/'evidence/sdk/registry.json').write_text(json.dumps({'dist':{'integrity':integrity}}),encoding='utf-8')
class SdkInventory(unittest.TestCase):
    def test_extra_files_prevent_a_misleading_exact_source_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            with patch.object(progress,'ROOT',root):
                self.assertIn('| Published SDK source | 1 / 1 files | 100% |',progress.render())
                for name in ['extra.ts','nested/extra.json','.extra.ts']:
                    extra=root/'packages/sdk/src'/name;extra.parent.mkdir(parents=True,exist_ok=True);extra.write_bytes(b'{}')
                    with self.assertRaisesRegex(ValueError,'SDK source inventory'):progress.render()
                    extra.unlink()
