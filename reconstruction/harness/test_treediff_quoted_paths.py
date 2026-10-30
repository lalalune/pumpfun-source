import subprocess
import unittest
from unittest.mock import patch
import treediff


class QuotedPathsTests(unittest.TestCase):
    def test_git_parser_retains_unusual_path_bytes(self):
        for name in ('src/a\tb.rs', 'src/a\nb.rs', 'src/a\x01b.rs', 'src/한글.rs', 'src/a"b.rs'):
            with self.subTest(name=name), patch.object(treediff, 'tree_files', side_effect=[
                    {name: b'old\n'}, {name: b'new\n'}]):
                text = treediff.tree_diff('before', 'after')
                result = subprocess.run(['git', 'apply', '--numstat', '-z', '-'],
                                        input=text.encode('utf-8'), capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b'1\t1\t' + ('programs/pump/' + name).encode('utf-8') + b'\0')


if __name__ == '__main__': unittest.main()
