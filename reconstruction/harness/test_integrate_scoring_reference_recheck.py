#!/usr/bin/env python3
"""A build that rewrites the scorer's reference inputs must not receive a score.

Sibling of merged #2945 (build_score_pair rechecks its bound sources and tools
after the paired build) and of test_integrate_build_input_recheck.py, which
guards the composed source, the baseline and score.py itself. score.py also
reads its reference ELF and window inventory through BASE
(reconstruction/base/original.so and functions.tsv) and imports the modules
beside the scorer. integrate.py builds the composition with arbitrary
build-script code and then scores against those same files, so a build script
that rewrites the reference ELF -- or a scorer import -- leaves the guard
unchanged and publishes a score against a doctored reference.

Only the binding helper is exercised; the fake SC/H roots keep the test off the
real repository tree.
"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate

INVENTORY = (b'program\tvariant\tscore\toriginal_start\toriginal_end\n'
             b'pump\tselected\t1\t4096\t4104\n')


class ScoringReferenceRecheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.sc = root / 'sc'
        self.harness = root / 'harness'
        self.harness.mkdir()
        self.scorer = self.harness / 'score.py'
        self.scorer.write_text('# scorer\n', encoding='utf-8')
        self.support = self.harness / 'score_admission.py'
        self.support.write_text('SCALE = 1\n', encoding='utf-8')
        self.base = self.sc / 'base'
        self.base.mkdir(parents=True)
        self.reference = self.base / 'original.so'
        self.reference.write_bytes(b'\x7fELF original capture\n')
        self.inventory = self.base / 'functions.tsv'
        self.inventory.write_bytes(INVENTORY)
        self.baseline = self.sc / 'baseline.json'
        self.baseline.write_text('{}\n', encoding='utf-8')
        self.src = root / 'src'
        self.src.mkdir()
        (self.src / 'lib.rs').write_text('pub fn fixture() {}\n', encoding='utf-8')

        self.patchers = [mock.patch.object(integrate, 'SC', self.sc),
                         mock.patch.object(integrate, 'H', self.harness)]
        for patcher in self.patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(self.patchers)])

    def bound(self):
        return integrate.bound_scoring_inputs(self.src, self.baseline)

    def assert_rewrite_changes_binding(self, path, replacement):
        """Change one file inside the guard and require the binding to move."""
        original = path.read_bytes()
        before = self.bound()
        try:
            path.write_bytes(replacement)
            self.assertNotEqual(self.bound(), before,
                                f'rewriting {path.name} left the binding unchanged')
        finally:
            path.write_bytes(original)
        self.assertEqual(self.bound(), before)

    def test_rewritten_reference_elf_changes_the_binding(self):
        # score.py reads resolve_original(BASE/'original.so'): a build that
        # edits one instruction of the reference ELF scores against it.
        self.assert_rewrite_changes_binding(self.reference, b'\x7fELF doctored capture\n')

    def test_rewritten_window_inventory_changes_the_binding(self):
        self.assert_rewrite_changes_binding(
            self.inventory,
            b'program\tvariant\tscore\toriginal_start\toriginal_end\n'
            b'pump\tselected\t1\t4096\t8192\n')

    def test_rewritten_scorer_support_module_changes_the_binding(self):
        # score.py imports score_admission, original_input, elf_symbols and
        # friends; hashing only score.py leaves those rewritable.
        self.assert_rewrite_changes_binding(self.support, b'SCALE = 0\n')

    def test_unchanged_inputs_keep_a_stable_binding(self):
        # The binding is the contract: these inputs, at these digests. Comparing
        # two calls with each other only catches nondeterminism - a binding that
        # stopped covering the inventory, the support modules or the baseline
        # would still equal its own second reading.
        digest = lambda data: hashlib.sha256(data).hexdigest()
        scorer = digest(b'# scorer\n')
        self.assertEqual(self.bound(), {
            'source': {'lib.rs': digest(b'pub fn fixture() {}\n')},
            'baseline': digest(b'{}\n'),
            'reference': {'original.so': digest(b'\x7fELF original capture\n'),
                          'functions.tsv': digest(INVENTORY)},
            'support': {'score.py': scorer, 'score_admission.py': digest(b'SCALE = 1\n')},
            'scorer': scorer,
        })


if __name__ == '__main__':
    unittest.main()
