"""A digest binding must bind at least one file.

Every check of the form ``all(sha(path) == digest for path, digest in m.items())``
is true for ``m == {}``, so a receipt, manifest or cache record that names no
input is accepted as if every input had been verified. ``finish`` in
``pump_text_layout.py`` shows the whole failure: a link record with an empty
``helper_sha256`` passes and reports ``bound_inputs: 0``.
"""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import pump_text_layout  # noqa: E402  — imported for its real link-record check


# (path, non-empty guard, the binding it protects, how many times the guard appears)
SITES = [
    ('scripts/pump_text_layout.py',
     "check(record['helper_sha256'], 'helper hash binding is empty')",
     "record['helper_sha256'].items()", 1),
    ('scripts/pump_replay_macos_frontier.py',
     "assert manifest, 'replay input manifest binds no source'",
     'manifest.items()', 1),
    ('scripts/pump_dependency_cache.py',
     'check(r["source_sha256"], "cache verification failed: clean build binds no source")',
     'r["source_sha256"].items()', 1),
    ('scripts/pump_data_order.py',
     'assert context["sdk"], \'baseline SDK binding is empty\'',
     'context["sdk"].items()', 1),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def link_record(directory, helpers):
    (directory / 'script.ld').write_text('SECTIONS {}\n')
    (directory / 'rust-lld').write_bytes(b'linker')
    (directory / 'wrapper.sh').write_bytes(b'wrapper')
    receipt = directory / 'linker-invocation.json'
    receipt.write_text(json.dumps({
        'incoming': [], 'link_inputs': {}, 'forwarded': [],
        'replacement_script_sha256': sha(directory / 'script.ld'),
        'real_linker_sha256': sha(directory / 'rust-lld')}))
    return {'script': str(directory / 'script.ld'),
            'script_sha256': sha(directory / 'script.ld'),
            'real_linker': str(directory / 'rust-lld'),
            'real_linker_sha256': sha(directory / 'rust-lld'),
            'external_wrapper': str(directory / 'wrapper.sh'),
            'external_wrapper_sha256': sha(directory / 'wrapper.sh'),
            'helper_sha256': helpers,
            'link_receipt': str(receipt)}


class EmptyBindingTests(unittest.TestCase):
    def test_a_link_record_that_binds_no_helper_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(AssertionError, 'helper hash binding is empty'):
                pump_text_layout.finish(link_record(directory, {}))

    def test_a_link_record_with_one_helper_still_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            helper = directory / 'helper.py'
            helper.write_bytes(b'helper')
            verified = pump_text_layout.finish(
                link_record(directory, {str(helper): sha(helper)}))
            self.assertEqual(verified['linker_invocation_sha256'],
                             sha(directory / 'linker-invocation.json'))

    def test_every_binding_refuses_an_empty_map(self):
        for name, guard, binding, expected in SITES:
            text = (ROOT / name).read_text(encoding='utf-8')
            with self.subTest(file=name, binding=binding):
                self.assertIn(binding, text, 'the binding this guard protects is gone')
                self.assertEqual(text.count(guard), expected,
                                 f'{name} no longer refuses an empty {binding}')


if __name__ == '__main__':
    unittest.main()
