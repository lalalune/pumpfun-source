import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from compare_scores import main


class DuplicateScoreFieldTests(unittest.TestCase):
    def test_duplicate_fields_cannot_silently_replace_memberships(self):
        good = '{"windows":{"0":{"bytes":8,"normalized":true,"raw":false}}}'
        bad = [
            '{"windows":{"0":{"bytes":8,"normalized":true,"raw":true}},"windows":{"0":{"bytes":8,"normalized":true,"raw":false}}}',
            '{"windows":{"0":{"bytes":8,"normalized":true,"raw":true},"0":{"bytes":8,"normalized":true,"raw":false}}}',
            '{"windows":{"0":{"bytes":8,"normalized":true,"raw":true,"raw":false}}}',
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, after = root/'before.json', root/'after.json'
            for invalid in bad:
                for side in ('baseline', 'candidate'):
                    with self.subTest(invalid=invalid, side=side):
                        before.write_text(invalid if side == 'baseline' else good, encoding='utf-8')
                        after.write_text(invalid if side == 'candidate' else good, encoding='utf-8')
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            with self.assertRaises(SystemExit) as error:
                                main([str(before), str(after)])
                        self.assertEqual(error.exception.code, 2)
            before.write_text(good, encoding='utf-8')
            after.write_text(good, encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([str(before), str(after)]), 0)
            self.assertTrue(json.loads(output.getvalue())['accepted'])


if __name__ == '__main__': unittest.main()
