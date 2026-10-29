"""Exercise ownership drift against the retained shell without running its JS."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('icons', APP/'scripts/extract-shell-icons.py')
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)


class ShellIconOwners(unittest.TestCase):
    def test_retained_search_icon_uses_its_search_landmark(self):
        _, body = icons.captured(icons.manifest()['records'], icons.HOME)
        segment = icons.shell_segment(body.decode('utf-8'))
        found = list(icons.SVG.finditer(segment))
        self.assertEqual(len(found), 42)
        self.assertEqual(icons.owner(segment, found[23].start()), {'role:search'})
        for position, _, expected in icons.HOME_ICONS:
            if expected is not None:
                self.assertIn(expected, icons.owner(segment, found[position].start()))
        outputs = icons.generate()
        bindings = json.loads((APP/'packages/frontend/SHELL-INTEGRATION-BINDINGS.json').read_text(encoding='utf-8'))
        for path, expected in outputs.items():
            self.assertEqual(hashlib.sha256(expected).hexdigest(), bindings['generated_assets'][path.relative_to(APP).as_posix()])

    def test_moving_retained_home_icon_outside_its_link_is_rejected(self):
        records = icons.manifest()['records']
        with tempfile.TemporaryDirectory(prefix='shell-owner-') as tmp:
            root = Path(tmp)
            needed = {icons.HOME, icons.LOGO_URL, *(url for url, _, _ in icons.ACTIVE_ICONS)}
            selected = [dict(r) for r in records if r['url'] in needed]
            for record in selected:
                data = (APP/record['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])
                if record['url'] == icons.HOME:
                    text = data.decode('utf-8')
                    segment = icons.shell_segment(text)
                    found = list(icons.SVG.finditer(segment))
                    item = found[1]
                    close = segment.index('</a>', item.end())
                    moved = segment[:item.start()] + segment[item.end():close+4] + item.group() + segment[close+4:]
                    self.assertEqual(icons.SVG.findall(moved), icons.SVG.findall(segment))
                    data = text.replace(segment, moved, 1).encode('utf-8')
                    record.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
                target = root/record['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            (root/'evidence/web/manifest.json').write_text(json.dumps({'records': selected}), encoding='utf-8')
            with patch.object(icons, 'ROOT', root):
                with self.assertRaisesRegex(SystemExit, 'NavHomeIcon.*not owned by href:/'):
                    icons.generate()

    def test_closed_controls_void_elements_and_encoded_attributes(self):
        for source in ['<a href="/">old</a><img><svg>', '<button aria-label="old"></button><br/><svg>']:
            self.assertEqual(icons.owner(source, source.index('<svg>')), set())
        source = '<a href="/?a=1&amp;b=2"><img><span><svg>'
        self.assertEqual(icons.owner(source, source.index('<svg>')), {'href:/?a=1&b=2'})


if __name__ == '__main__':
    unittest.main()
