import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_elf_symbols import fixture
import score


class AtomicScoreReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root/'base'; self.base.mkdir()
        self.image = bytes(fixture())
        (self.base/'original.so').write_bytes(self.image)
        (self.base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',encoding='utf-8')
        self.candidate, self.output = self.root/'candidate.so',self.root/'report.json'
        self.candidate.write_bytes(self.image)

    def run_score(self, after_admission=None):
        original = score.score_with_hash
        def read(path):
            if after_admission is not None: after_admission()
            return original(path)
        argv = ['score.py',str(self.candidate),'--no-baseline','--json',str(self.output)]
        with patch.object(score,'BASE',self.base), patch.object(score,'score_with_hash',side_effect=read), patch.object(sys,'argv',argv), contextlib.redirect_stdout(io.StringIO()):
            score.main()

    def test_destination_linked_to_candidate_after_admission_cannot_truncate_input(self):
        self.run_score(lambda:self.output.hardlink_to(self.candidate))
        self.assertEqual(self.candidate.read_bytes(),self.image)
        self.assertTrue(json.loads(self.output.read_text(encoding='utf-8'))['windows']['4096']['raw'])
        self.assertFalse(self.output.samefile(self.candidate))
        self.assertEqual(list(self.root.glob('.score-*')),[])

    def test_replacing_an_existing_report_remains_supported(self):
        self.output.write_text('old report',encoding='utf-8')
        self.run_score()
        self.assertTrue(json.loads(self.output.read_text(encoding='utf-8'))['windows']['4096']['raw'])
        self.assertEqual(self.candidate.read_bytes(),self.image)
        self.assertEqual(list(self.root.glob('.score-*')),[])

    def test_failed_publication_preserves_prior_report_and_cleans_temporary(self):
        self.output.write_bytes(b'prior receipt')
        with patch.object(Path,'replace',side_effect=PermissionError('publication denied')):
            with self.assertRaises(PermissionError): self.run_score()
        self.assertEqual(self.output.read_bytes(),b'prior receipt')
        self.assertEqual(self.candidate.read_bytes(),self.image)
        self.assertEqual(list(self.root.glob('.score-*')),[])


if __name__ == '__main__': unittest.main()
