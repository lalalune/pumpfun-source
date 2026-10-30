import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import log_attempt as ledger
from ledger_schema import inspect_ledger, validate_row


def row():
    return dict(schema='main-pump-attempt-v1',attempt_id='id',timestamp_utc='2026-10-29T00:00:00+00:00',lane='lane',approach='approach',target='all',dedupe_key='key',hypothesis='test',status='analyzed',data={})


class LedgerSchemaTests(unittest.TestCase):
    def test_committed_ledger_remains_valid(self):
        rows,errors=inspect_ledger(ledger.TRACKED.read_text(),ledger.STATUSES)
        self.assertEqual(errors,[]);self.assertGreater(len(rows),1000)

    def test_malformed_fields_rejected(self):
        for field,value in [('data',[]),('lane',' '),('status','invented'),('timestamp_utc','2026-10-29T00:00:00'),('schema','v2'),('data',{'metric':float('inf')})]:
            with self.subTest(field=field),self.assertRaises(ValueError):validate_row(row()|{field:value},ledger.STATUSES)

    def test_audit_reports_all_line_numbers(self):
        text='\n'.join([json.dumps(row()),'[]','not json',json.dumps(row())])
        rows,errors=inspect_ledger(text,ledger.STATUSES)
        self.assertEqual(len(rows),1);self.assertEqual([e['line'] for e in errors],[2,3,4])
        self.assertIn('first seen on line 1',errors[-1]['message'])

    def test_duplicate_json_keys_are_not_silently_replaced(self):
        text=json.dumps(row())[:-1]+',"data":{}}'
        _,errors=inspect_ledger(text,ledger.STATUSES)
        self.assertIn('duplicate JSON property',errors[0]['message'])

    def test_corrupt_live_rows_block_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger';path.write_text('[]\n')
            with patch.object(ledger,'LEDGER',path),self.assertRaisesRegex(SystemExit,'corrupt ledger line 1'):ledger.read_rows()

    def test_offline_audit_never_seeds_live_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'saved';path.write_text(json.dumps(row())+'\n')
            live=Path(temp)/'live'
            with patch.object(ledger,'LEDGER',live),patch('sys.argv',['ledger','audit','--path',str(path)]),contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(ledger.main(),0)
            self.assertTrue(json.loads(output.getvalue())['valid']);self.assertFalse(live.exists())

    def test_invalid_record_does_not_append(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger';path.write_text(json.dumps(row())+'\n');before=path.read_bytes()
            args=['ledger','record','--lane',' ','--approach','a','--target','all','--dedupe-key','new','--hypothesis','h','--status','analyzed']
            with patch.object(ledger,'LEDGER',path),patch.object(ledger,'LOCK',Path(temp)/'lock'),patch('sys.argv',args),self.assertRaisesRegex(SystemExit,'invalid attempt'):ledger.main()
            self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':unittest.main()
