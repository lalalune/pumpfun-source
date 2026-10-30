"""Regressions for side-specific color names in the retained compiled stylesheet."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/extract-theme.py'
spec = importlib.util.spec_from_file_location('extract_theme_directional', SCRIPT)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class DirectionalBorderColors(unittest.TestCase):
    def test_retained_stylesheet_and_generated_outputs(self):
        record, css = theme.load_source()
        self.assertEqual(record['sha256'], '8bda96ca39398a46befb900a2d43a4e695ff9975ce6c4bb83c1f45bb47eced93')
        colors = theme.extract_colors(css)
        self.assertEqual(len(colors), 171)
        for name in ('l-bg-accent', 'l-positive', 'l-transparent', 't-blue-500',
                     't-positive', 't-transparent', 't-white'):
            self.assertNotIn(name, colors)
        for name in ('bg-accent', 'positive', 'transparent', 'blue-500', 'white'):
            self.assertIn(name, colors)
        generated = theme.generate()
        for path, content in generated.items():
            self.assertEqual(path.read_text(encoding='utf-8'), content)
        result = subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_direction_channels_and_variants(self):
        for prefix, properties in theme.DIRECTIONAL_BORDER_PROPERTIES.items():
            with self.subTest(prefix=prefix):
                body = ';'.join(prop + ':#123' for prop in properties)
                self.assertEqual(theme.extract_colors('.hover\\:' + prefix + '-brand:hover{' + body + '}'),
                                 {'brand': '#112233'})

    def test_plain_border_color_keeps_a_direction_shaped_theme_name(self):
        self.assertEqual(theme.extract_colors('.border-t-brand{border-color:#123}.border-l-brand{border-color:#456}'),
                         {'l-brand': '#445566', 't-brand': '#112233'})

    def test_directional_color_still_participates_in_conflict_check(self):
        with self.assertRaisesRegex(SystemExit, 'color.*brand'):
            theme.extract_colors('.bg-brand{background-color:#123}.border-l-brand{border-left-color:#456}')

    def test_widths_arbitrary_values_and_opacity_are_not_palette_keys(self):
        self.assertEqual(theme.extract_colors('.border-t-2{border-top-width:2px}.border-x-4{border-left-width:4px;border-right-width:4px}'
                         '.border-l-brand\\/50{border-left-color:#123}.border-l-\\[red\\]{border-left-color:red}'), {})


if __name__ == '__main__':
    unittest.main()
