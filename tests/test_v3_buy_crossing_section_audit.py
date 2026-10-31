"""Admission controls for the v3 buy-crossing applied data-section comparison."""
import importlib.util
from pathlib import Path
import unittest

LANE = Path(__file__).resolve().parents[1] / 'reconstruction/pump-main/lanes/v3-buy-crossing-layout'


def load():
    spec = importlib.util.spec_from_file_location('v3_buy_crossing_packet', LANE / 'verify_packet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SectionComparisonTests(unittest.TestCase):
    def setUp(self):
        self.verify = load()

    def audit(self, sections):
        return {'sections_equal': sections}

    def test_both_sections_equal_is_accepted(self):
        self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': True}))

    def test_changed_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data sections changed'):
            self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': False}))

    def test_truthy_non_boolean_comparison_is_rejected(self):
        for value in (1, 'true', ['equal'], {'.text': True}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'applied data sections changed'):
                self.verify.check_sections(self.audit({'.rodata': True, '.data.rel.ro': value}))

    def test_section_name_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit(['.rodata', '.data.rel.ro']))

    def test_empty_comparison_is_rejected(self):
        # all({}.values()) is True, so an emptied audit used to pass the check.
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit({}))

    def test_dropped_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit({'.rodata': True}))

    def test_unexpected_section_is_rejected(self):
        sections = {'.rodata': True, '.data.rel.ro': True, '.text': True}
        with self.assertRaisesRegex(ValueError, 'applied data section set changed'):
            self.verify.check_sections(self.audit(sections))


if __name__ == '__main__':
    unittest.main()
