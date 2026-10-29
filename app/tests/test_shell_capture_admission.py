"""Shell generators must authenticate the selected capture, not only its hash."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

APP=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,APP/f'scripts/{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
icons=load('extract-shell-icons')
theme=load('extract-theme')


class ShellCaptureAdmission(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='shell-capture-')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        records=json.loads((APP/'evidence/web/manifest.json').read_text(encoding='utf-8'))['records']
        urls={icons.HOME,icons.LOGO_URL,theme.SOURCE_URL,*(url for url,_,_ in icons.ACTIVE_ICONS)}
        self.records=[copy.deepcopy(record) for record in records if record['url'] in urls]
        for record in self.records:
            body=(APP/record['path']).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(),record['sha256'])
            self.assertEqual(len(body),record['bytes'])
            path=self.root/record['path']
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(body)

    def generate(self,module,rows):
        (self.root/'evidence/web/manifest.json').write_text(json.dumps({'records':rows}),encoding='utf-8')
        with patch.object(module,'ROOT',self.root):
            return module.generate()

    def test_unchanged_retained_captures_keep_the_bound_generated_assets(self):
        expected=json.loads((APP/'packages/frontend/SHELL-INTEGRATION-BINDINGS.json').read_text(encoding='utf-8'))['generated_assets']
        for module in [icons,theme]:
            for path,body in self.generate(module,self.records).items():
                if isinstance(body,str):body=body.encode('utf-8')
                self.assertEqual(hashlib.sha256(body).hexdigest(),expected[path.relative_to(APP).as_posix()])

    def test_wrong_status_or_declared_size_cannot_generate_source_bound_assets(self):
        for module,url in [(icons,icons.HOME),(theme,theme.SOURCE_URL)]:
            for field,value in [('status',404),('status','200'),('status',None),('bytes',1),('bytes',True),('bytes','1'),('bytes',None)]:
                with self.subTest(module=module.__name__,field=field,value=value):
                    rows=copy.deepcopy(self.records)
                    record=next(r for r in rows if r['url']==url)
                    if value is None:record.pop(field)
                    else:record[field]=value
                    with self.assertRaisesRegex(SystemExit,'successful capture|byte count'):
                        self.generate(module,rows)

    def test_duplicate_url_records_are_ambiguous_even_with_identical_bytes(self):
        for module,url in [(icons,icons.HOME),(theme,theme.SOURCE_URL)]:
            with self.subTest(module=module.__name__):
                rows=copy.deepcopy(self.records)
                rows.append(copy.deepcopy(next(r for r in rows if r['url']==url)))
                with self.assertRaisesRegex(SystemExit,'one capture'):
                    self.generate(module,rows)


if __name__=='__main__':unittest.main()
