"""The guarded generator must admit the reviewed sources of the current checkout."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guarded = load('roadmap_reviewed_generate', PACKAGE / 'generate.py')
sibling = load('roadmap_dynamic_generate', ROOT / 'reconstruction/diagnostics/defined-dynamic-calls/generate.py')


class CurrentPinTests(unittest.TestCase):
    def test_pins_agree_with_the_sibling_roadmap_diagnostic(self):
        # The two diagnostics execute different input sets (the guarded one
        # also pins the archived roadmap snapshot; the sibling also pins the
        # ELF reader), so agreement is required on the sources both review:
        # a shared source must never carry diverging reviewed digests.
        shared = set(guarded.REVIEWED) & set(sibling.REVIEWED)
        self.assertEqual(shared, {guarded.SOURCE, guarded.ARCHIVE})
        for name in shared:
            self.assertEqual(guarded.REVIEWED[name], sibling.REVIEWED[name], name)

    def test_current_checkout_is_admitted(self):
        try:
            bindings = guarded.admitted_inputs(ROOT)
        except ValueError as error:
            self.fail(str(error))
        self.assertEqual(set(bindings), set(guarded.REVIEWED))


if __name__ == '__main__':
    unittest.main()
