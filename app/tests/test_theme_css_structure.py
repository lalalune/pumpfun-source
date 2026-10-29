"""Derive shell rules from retained CSS without treating token data as braces."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

APP=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('theme_structure',APP/'scripts/extract-theme.py')
theme=importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class ThemeCssStructure(unittest.TestCase):
    def generated(self,css):
        record,_=theme.load_source()
        with tempfile.TemporaryDirectory(prefix='theme-css-') as tmp:
            root=Path(tmp)
            record=copy.deepcopy(record)
            data=css.encode('utf-8')
            record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            path=root/record['path']
            path.parent.mkdir(parents=True)
            path.write_bytes(data)
            (root/'evidence/web/manifest.json').write_text(json.dumps({'records':[record]}),encoding='utf-8')
            with patch.object(theme,'ROOT',root):return theme.generate()

    def test_original_retained_stylesheet_keeps_all_generated_hashes(self):
        _,css=theme.load_source()
        expected=json.loads((APP/'packages/frontend/SHELL-INTEGRATION-BINDINGS.json').read_text(encoding='utf-8'))['generated_assets']
        for path,text in self.generated(css).items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),expected[path.relative_to(APP).as_posix()])

    def test_real_stylesheet_with_static_brace_values_keeps_complete_shell_rules(self):
        _,css=theme.load_source()
        for body in ['content:"}"','content:"{"','/* } { */content:"x"','background-image:url(data:image/svg+xml,{)']:
            with self.subTest(body=body):
                rule='.pump-main-shell::before{'+body+'}'
                outputs=self.generated(css+'\n'+rule)
                self.assertIn(rule,outputs[theme.SHELL_CSS])

    def test_root_custom_property_strings_do_not_truncate_the_root_block(self):
        body='--label:"} {";--value:1'
        self.assertEqual(theme.root_block(':root{'+body+'}.other{color:red}'),body)
        _,css=theme.load_source()
        self.assertIn(':root{',css)
        outputs=self.generated(css.replace(':root{',':root{'+body+';',1))
        self.assertIn(body+';',outputs[theme.ROOT_CSS])

    def test_nested_at_rule_keeps_quoted_values_inside_its_shell_rule(self):
        rule='@media (min-width:1px){.pump-main-shell::before{content:"}"}}'
        self.assertEqual(theme.shell_rules('.pump-main-shell{display:flex}'+rule),['.pump-main-shell{display:flex}',rule])


if __name__=='__main__':unittest.main()
