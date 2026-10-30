import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from attempt_applicability import FIELDS, classify


class EvidenceRootPathTests(unittest.TestCase):
    def inspect(self, root, path, payload):
        context = {field:'a'*64 for field in FIELDS}
        row = {'data': {'context':context, 'evidence':[{'path':path,'sha256':hashlib.sha256(payload).hexdigest()}]}}
        return classify(row, context, root)

    @unittest.skipUnless(os.name == 'nt', 'Windows rooted-relative path semantics')
    def test_rooted_relative_path_cannot_admit_a_file_outside_evidence_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent/'evidence'; root.mkdir()
            outside = parent/'outside.json'; outside.write_bytes(b'outside retained evidence')
            rooted = str(outside)[len(outside.drive):]
            self.assertFalse(Path(rooted).is_absolute())
            self.assertEqual(root/Path(rooted), outside)
            result = self.inspect(root, rooted, outside.read_bytes())
            self.assertEqual(result['applicability'], 'unverifiable')
            self.assertIn('evidence path must remain within evidence root', result['reasons'])

    def test_relative_in_root_file_still_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'nested').mkdir()
            (root/'nested/result.json').write_bytes(b'{}')
            self.assertEqual(self.inspect(root, 'nested/result.json', b'{}')['applicability'], 'compatible')

    def test_absolute_and_parent_relative_paths_remain_unverifiable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root/'result.json'; path.write_bytes(b'{}')
            for name in (str(path), '../result.json'):
                with self.subTest(name=name):
                    self.assertEqual(self.inspect(root, name, b'{}')['applicability'], 'unverifiable')


if __name__ == '__main__': unittest.main()
