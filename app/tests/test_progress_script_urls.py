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
class ScriptUrls(unittest.TestCase):
    def test_queries_and_fragments_do_not_change_script_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);records=[]
            for index,url in enumerate(['https://example.test/a.js?v=1','https://example.test/a.js?v=2#part','https://example.test/page?next=a.js']):
                body=b'captured';path=f'evidence/web/objects/{index}';(root/path).write_bytes(body)
                records.append({'url':url,'status':200,'path':path,'sha256':hashlib.sha256(body).hexdigest()})
            (root/'evidence/web/manifest.json').write_text(json.dumps({'records':records}),encoding='utf-8')
            with patch.object(progress,'ROOT',root):text=progress.render()
            self.assertIn('| Frontend JavaScript capture | 2 / 2 scripts | 100% |',text)
