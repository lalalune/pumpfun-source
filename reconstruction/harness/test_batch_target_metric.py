import contextlib
import io
import json
import re
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import target_metric as metric

RAW=struct.pack('<BBhi',0x95,0,0,0)
WINDOWS=[{'start':start,'bytes':8,'raw':RAW,'norm':RAW} for start in (0,8)]


class Candidate:
    funcs=[(16,8,'first'),(24,8,'second')]
    secs={}
    def fn(self,start,size):return RAW


class BatchMetricTests(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.original=self.stack.enter_context(patch.object(metric,'original_windows',return_value=WINDOWS))
        self.candidate=self.stack.enter_context(patch.object(metric,'Cand',return_value=Candidate()))
        self.stack.enter_context(patch.object(metric,'best_candidates',return_value=[(1,1,16,8,'first')]))
        self.stack.enter_context(patch.object(metric,'demangle',side_effect=lambda name:name))
        self.output=self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))

    def test_batch_loads_candidate_and_inventory_once(self):
        self.assertEqual(metric.main(['candidate.so','0x0','8']),0)
        self.candidate.assert_called_once();self.original.assert_called_once()
        rows=[json.loads(line) for line in self.output.getvalue().splitlines()]
        self.assertEqual([row['window'] for row in rows],['0x0','0x8'])
        self.assertTrue(all(row['normalized_equal'] and row['raw_equal'] for row in rows))
        self.assertTrue(all(row['call_counts_original'] == {
            'internal': 0, 'syscall_or_relocated': 0, 'indirect': 0,
        } for row in rows))

    def test_duplicates_are_coalesced_in_request_order(self):
        metric.main(['candidate.so','8','0','0x8'])
        self.assertEqual([json.loads(line)['window'] for line in self.output.getvalue().splitlines()],['0x8','0x0'])

    def test_unknown_target_rejects_entire_batch_before_loading_candidate(self):
        with self.assertRaises(SystemExit) as caught:metric.main(['candidate.so','0','999'])
        self.assertEqual(caught.exception.code,2);self.candidate.assert_not_called()
        self.assertEqual(self.output.getvalue(),'')

    def test_invalid_options_are_rejected_before_loading_inputs(self):
        for extra in [['--top','0'],['--slots','-1'],['--sym','[']]:
            with self.assertRaises(SystemExit):metric.main(['candidate.so','0',*extra])
        self.original.assert_not_called();self.candidate.assert_not_called()

    def test_symbol_selection_keeps_all_matches_per_window(self):
        metric.main(['candidate.so','0','8','--sym','first|second','--top','1'])
        self.assertEqual(len(self.output.getvalue().splitlines()),4)

    def test_json_export_matches_json_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'nested/report.json'
            metric.main(['candidate.so','0','8','--json',str(path)])
            self.assertEqual(json.loads(path.read_text()),[json.loads(line) for line in self.output.getvalue().splitlines()])

    def test_single_window_api_and_zero_offset_detail_limit(self):
        rows=metric.measure_window(WINDOWS[0],Candidate(),re.compile('first'),slots=0)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['first_diff_offsets'],[])


if __name__=='__main__':unittest.main()
