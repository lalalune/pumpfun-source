import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-shell-icons.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class ShellBoundary(unittest.TestCase):

    def test_missing_script_does_not_become_negative_slice_end(self):
        fragment = '<div hidden id="S:2"><main data-app-shell=""><svg></svg></main></div>'
        with self.assertRaisesRegex(SystemExit, 'boundary'):
            subject.shell_segment(fragment)
        self.assertEqual(subject.shell_segment(fragment + '<script>tail</script>'), fragment)
