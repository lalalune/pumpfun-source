"""SDK discovery for disassembly and independent native symbol reading."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import llvm_tools
import score
import win
from test_elf_symbols import fixture
from elf_symbols import function_symbols


class ObjdumpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {'PATH': str(self.root)}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.home = patch.object(Path, 'home', return_value=self.root)
        self.home.start()
        self.addCleanup(self.home.stop)

    def executable(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/sh\ncase "$1" in\n-t) printf "00000120 g F .text 00000010 example\\n";;\n-d) printf " 120: exit\\n";;\n*) exit 2;;\nesac\n')
        path.chmod(0o755)
        return path

    def sdk(self, version):
        return self.executable(self.root / '.cache/solana' / version / 'platform-tools/llvm/bin/llvm-objdump')

    def test_documented_sdk_and_legacy_preference(self):
        current = self.sdk('v1.44')
        self.assertEqual(llvm_tools.objdump(), str(current))
        legacy = self.sdk('v1.52')
        self.assertEqual(llvm_tools.objdump(), str(legacy))

    def test_path_and_explicit_override(self):
        fallback = self.executable(self.root / 'llvm-objdump')
        self.assertEqual(llvm_tools.objdump(), str(fallback))
        self.sdk('v1.52')
        selected = self.executable(self.root / 'custom tool')
        os.environ['PUMP_OBJDUMP'] = str(selected)
        self.assertEqual(llvm_tools.objdump(), str(selected))

    def test_invalid_override_does_not_fall_back(self):
        self.sdk('v1.44')
        for value in ('', 'missing', str(self.root)):
            with self.subTest(value=value), patch.dict(os.environ, {'PUMP_OBJDUMP': value}):
                with self.assertRaisesRegex(FileNotFoundError, 'PUMP_OBJDUMP'):
                    llvm_tools.objdump()

    def test_missing_tool_has_actionable_error(self):
        with self.assertRaisesRegex(FileNotFoundError, 'v1.44 SDK'):
            llvm_tools.objdump()

    def test_non_executable_sdk_is_skipped(self):
        bad = self.sdk('v1.52')
        bad.chmod(0o644)
        selected = self.sdk('v1.44')
        self.assertEqual(llvm_tools.objdump(), str(selected))

    def test_native_symbols_and_disassembly_override_coexist(self):
        selected = self.executable(self.root / 'tool with spaces')
        os.environ['PUMP_OBJDUMP'] = str(selected)
        candidate = self.root / 'candidate.so'
        candidate.write_bytes(fixture())
        with patch.object(llvm_tools, 'objdump', side_effect=AssertionError('symbols must not discover SDK')):
            self.assertEqual(score.candidate_functions(candidate), function_symbols(fixture()))
        self.assertEqual(win.objdump_text(self.root / 'candidate.so', 0x120, 0x130), {0x120: 'exit'})


if __name__ == '__main__':
    unittest.main()
