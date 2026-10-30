"""Regression tests: verdict publication must not follow a planted link.

evaluate() used to publish verdict.json at its fixed name with a plain
write_text, so a symlink planted at the verdict path redirected the write
into an unrelated file and the published verdict itself stayed a symlink.
Publication now stages through an exclusively created, unpredictable
sibling (the score.write_report pattern) and replaces the destination.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import match_oracle as oracle


class VerdictStagingTests(unittest.TestCase):
    def run_evaluate(self, root, out, work_name='work'):
        for name in ['original.so', 'functions.tsv']:
            (root / name).write_bytes(b'fixture')
        with patch.object(oracle.score, 'BASE', root), \
                patch.object(oracle.score, 'original_windows',
                             return_value=[{'start': 8}]), \
                patch.object(oracle.fastbuild, 'build',
                             return_value={'ok': False}):
            return oracle.evaluate(root, root / work_name, out, 8,
                                   'normalized', 'identity')

    def test_planted_verdict_symlink_is_replaced_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'out'; out.mkdir()
            victim = root / 'victim.json'
            victim.write_text('{"sentinel": "do-not-touch"}\n')
            (out / 'verdict.json').symlink_to(victim)
            self.assertEqual(self.run_evaluate(root, out), 2)
            self.assertEqual(victim.read_text(), '{"sentinel": "do-not-touch"}\n',
                             'publication followed the planted verdict symlink')
            verdict = out / 'verdict.json'
            self.assertFalse(verdict.is_symlink(),
                             'published verdict must be a regular file')
            self.assertEqual(json.loads(verdict.read_text())['status'], 'error')

    def test_verdict_still_published_and_replaced_on_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'out'; out.mkdir()
            self.assertEqual(self.run_evaluate(root, out), 2)
            verdict = out / 'verdict.json'
            self.assertTrue(verdict.is_file() and not verdict.is_symlink())
            self.assertEqual(json.loads(verdict.read_text())['status'], 'error')
            # A second run replaces the previous verdict as before.
            self.assertEqual(self.run_evaluate(root, out, 'work2'), 2)
            self.assertEqual(json.loads(verdict.read_text())['status'], 'error')
            self.assertEqual(list(out.glob('.verdict-*')), [],
                             'no staging files may be left behind')


    def test_failed_flush_preserves_existing_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); verdict = root / 'verdict.json'
            verdict.write_bytes(b'previous verdict')
            with patch.object(oracle.os, 'fsync', side_effect=OSError('fsync failure')):
                with self.assertRaisesRegex(OSError, 'fsync failure'):
                    oracle.publish_verdict(verdict, 'new verdict\n')
            self.assertEqual(verdict.read_bytes(), b'previous verdict')
            self.assertEqual(list(root.glob('.verdict-*')), [])

    def test_consumed_stage_is_not_deleted_if_another_writer_recreates_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); verdict = root / 'verdict.json'
            original = Path.replace; recreated = []
            def replace(source, destination):
                result = original(source, destination)
                source.write_bytes(b'other writer'); recreated.append(source)
                return result
            with patch.object(Path, 'replace', replace):
                oracle.publish_verdict(verdict, 'new verdict\n')
            self.assertEqual(verdict.read_bytes(), b'new verdict\n')
            self.assertEqual(recreated[0].read_bytes(), b'other writer')

    def test_failed_replace_does_not_delete_another_writers_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); verdict = root / 'verdict.json'
            verdict.write_bytes(b'previous verdict'); recreated = []
            def replace(source, destination):
                source.rename(root / 'moved-stage')
                source.write_bytes(b'other writer'); recreated.append(source)
                raise OSError('replacement failed')
            with patch.object(Path, 'replace', replace):
                with self.assertRaisesRegex(OSError, 'replacement failed'):
                    oracle.publish_verdict(verdict, 'new verdict\n')
            self.assertEqual(verdict.read_bytes(), b'previous verdict')
            self.assertEqual(recreated[0].read_bytes(), b'other writer')



if __name__ == '__main__':
    unittest.main()
