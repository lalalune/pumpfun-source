"""Run actual resume/discovery/publication using authenticated retained objects."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('capture_redirect_base',Path(__file__).resolve().parents[1]/'scripts/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)

def resume(root,objects):
    out=root/'evidence/web';(out/'objects').mkdir(parents=True)
    records=[]
    objects={**objects,'https://docs.pump.fun/openapi.public.json':(b'{}',None),'https://docs.pump.fun/llms-full.txt':(b'',None)}
    for index,(url,(body,final_url)) in enumerate(objects.items()):
        path=f'evidence/web/objects/object-{index}'
        (root/path).write_bytes(body)
        record={'url':url,'status':200,'path':path,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        if final_url is not None: record['final_url']=final_url
        records.append(record)
    (out/'manifest.json').write_text(json.dumps({'records':records}),encoding='utf-8')
    with patch.object(capture,'ROOT',root),patch.object(capture,'OUT',out),patch.object(capture,'PAGES',['/']),patch.object(capture,'REUSE',{}),patch('sys.argv',['capture.py','--resume']):
        capture.main()
    return json.loads((out/'manifest.json').read_text(encoding='utf-8'))

class RedirectBase(unittest.TestCase):
    def test_css_relative_dependencies_resolve_against_the_final_response_url(self):
        for final in ['https://pump.fun/new/theme.css?v=2',None]:
            with self.subTest(final=final),tempfile.TemporaryDirectory() as tmp:
                objects={
                    'https://pump.fun/':(b'<link href="/old/style.css?v=1">',None),
                    'https://pump.fun/old/style.css?v=1':(b'@font-face{src:url("fonts/a.woff2?v=3#font")}',final),
                    'https://pump.fun/new/fonts/a.woff2?v=3':(b'final font',None),
                    'https://pump.fun/old/fonts/a.woff2?v=3':(b'old font',None),
                }
                result=resume(Path(tmp),objects)
                urls={r['url'] for r in result['records']}
                expected='new' if final else 'old';other='old' if final else 'new'
                self.assertIn(f'https://pump.fun/{expected}/fonts/a.woff2?v=3',urls)
                self.assertNotIn(f'https://pump.fun/{other}/fonts/a.woff2?v=3',urls)
                css=next(r for r in result['records'] if r['url'].endswith('style.css?v=1'))
                self.assertEqual(css.get('final_url',css['url']),final or css['url'])

    def test_redirected_external_html_does_not_invent_same_host_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=resume(Path(tmp),{
                'https://pump.fun/':(b'<script src="/foreign.js"></script>','https://docs.pump.fun/redirected'),
                'https://pump.fun/foreign.js':(b'const wrongOrigin=true;',None),
            })
            self.assertNotIn('https://pump.fun/foreign.js',{r['url'] for r in result['records']})
