import importlib.util
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', ROOT / 'scripts/analyze.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)
import base64, struct, subprocess

def fixture():
    b = bytearray(128)
    b[:16] = b'\x7fELF\x02\x01\x01' + bytes(9)
    struct.pack_into('<HHIQQQIHHHHHH', b, 16, 3, 247, 1, 0, 0, 64, 0, 64, 56, 0, 64, 1, 0)
    return b

class OptimizedElf(unittest.TestCase):

    def test_optimization_does_not_turn_invalid_layout_into_a_receipt(self):
        valid = fixture()
        self.assertEqual(subject.elf_layout(valid)['elf_extent'], 128)
        identity = fixture()
        identity[:4] = b'bad!'
        extent = fixture()
        struct.pack_into('<IIQQQQIIQQ', extent, 64, 0, 1, 0, 0, 1000, 8, 0, 0, 1, 0)
        script = "import sys,base64;sys.path.insert(0,sys.argv[1]);from analyze import elf_layout\ntry:elf_layout(base64.b64decode(sys.argv[2]))\nexcept (ValueError,AssertionError):print('rejected')\nelse:print('accepted')"
        for data in [identity, extent]:
            for optimized in [[], ['-O']]:
                with self.subTest(optimized=optimized):
                    result = subprocess.check_output([sys.executable, *optimized, '-c', script, str(ROOT / 'scripts'), base64.b64encode(data).decode()], text=True)
                    self.assertEqual(result.strip(), 'rejected')
