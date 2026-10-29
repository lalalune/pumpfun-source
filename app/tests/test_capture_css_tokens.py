"""Real --resume capture workflow with authenticated retained CSS and fonts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('capture_css', APP/'scripts/capture.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class CaptureCssTokens(unittest.TestCase):
    def test_real_retained_stylesheet_dependencies_ignore_inert_text(self):
        manifest = json.loads((APP/'evidence/web/manifest.json').read_text(encoding='utf-8'))
        css_record = next(r for r in manifest['records'] if r.get('path') == 'evidence/web/objects/26bc2224429aacd3.css')
        original = (APP/css_record['path']).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), '8faed4840b5b667adc6f5b368301c05a692a937dd1acc51defa45a17f72b2944')
        fonts = {capture.public_asset(value, css_record['url'], ('.woff2','.woff','.ttf')) for value in re.findall(r'url\(([^)]+)\)', original.decode('utf-8'))}
        fonts.discard(None)
        self.assertEqual(len(fonts), 12)
        fake = {f'https://pump.fun/_next/static/media/{kind}.woff2' for kind in ['comment', 'string', 'other-function']}
        suffix = b'\n/* url("/_next/static/media/comment.woff2") */\n.x{content:\'url("/_next/static/media/string.woff2")\';--x:myurl("/_next/static/media/other-function.woff2")}\n'
        for derived in [False, True]:
            with self.subTest(derived=derived), tempfile.TemporaryDirectory(prefix='capture-css-') as tmp:
                root = Path(tmp)
                (root/'scripts').mkdir()
                shutil.copyfile(APP/'scripts/capture.py', root/'scripts/capture.py')
                objects = root/'evidence/web/objects'
                objects.mkdir(parents=True)
                rows = []
                def retain(url, body, status=200):
                    digest = hashlib.sha256(body).hexdigest()
                    path = 'evidence/web/objects/'+hashlib.sha256(url.encode()).hexdigest()[:16]
                    (root/path).write_bytes(body)
                    rows.append(dict(url=url,final_url=url,status=status,path=path,sha256=digest,bytes=len(body),headers={}))
                for url in ['https://pump.fun'+p for p in capture.PAGES]+['https://docs.pump.fun/openapi.public.json','https://docs.pump.fun/llms-full.txt']:
                    retain(url, ('<link href="'+css_record['url'].replace('https://pump.fun','')+'">').encode() if url=='https://pump.fun/' else b'')
                css = original+suffix if derived else original
                retain(css_record['url'], css)
                for url in fonts:
                    record = next(r for r in manifest['records'] if r['url']==url)
                    body = (APP/record['path']).read_bytes()
                    self.assertEqual(hashlib.sha256(body).hexdigest(),record['sha256'])
                    retain(url,body)
                for url in fake: retain(url,b'unused retained control')
                (root/'evidence/web/manifest.json').write_text(json.dumps({'records':rows}),encoding='utf-8')
                # A real CLI subprocess reads retained objects. Audit rejection
                # forbids network access; it does not simulate a response.
                launcher = "import runpy,sys\ndef guard(event,args):\n if event in ('socket.connect','socket.getaddrinfo'): raise AssertionError('network forbidden')\nsys.addaudithook(guard)\nsys.argv=['capture.py','--resume']\nrunpy.run_path('scripts/capture.py',run_name='__main__')"
                result = subprocess.run([sys.executable,'-c',launcher],cwd=root,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                output = json.loads((root/'evidence/web/manifest.json').read_text(encoding='utf-8'))
                urls = {r['url'] for r in output['records']}
                self.assertTrue(fonts.issubset(urls),fonts-urls)
                self.assertFalse(fake & urls,fake & urls)
                self.assertEqual((root/next(r['path'] for r in rows if r['url']==css_record['url'])).read_bytes(),css)

    def test_css_token_forms_are_decoded_without_promoting_strings_or_comments(self):
        source = r'''/* url(comment.svg) */ .x{content:"url(string.svg)";a:URL('a.svg');b:url(escaped\)name.svg);c:url("\61 .svg");d:image-set(url(nested.svg) 1x);e:myurl(other.svg)}'''
        self.assertEqual(list(capture.literal_css_urls(source)), ['a.svg','escaped)name.svg','a.svg','nested.svg'])


if __name__ == '__main__': unittest.main()
