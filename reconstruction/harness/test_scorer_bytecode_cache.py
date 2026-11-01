#!/usr/bin/env python3
"""A cache entry written beside the harness must not decide the score.

score.py imports the modules beside it (llvm_tools, original_input,
score_admission, elf_symbols, instruction_stream). CPython executes a cached
module whenever the __pycache__ header matches the source's mtime and size, so a
cache written for an *unmodified* source runs in place of that source and leaves
every digest integrate.py binds unchanged. -B and -I stop imports from writing
bytecode; they do not stop them from reading it.

integrate.py runs the build first -- arbitrary build-script code -- and starts
score.py afterwards, so a build script can write that cache entry and decide
what the scorer executes while `support` still digests the same bytes.
"""

import importlib.util
import os
import py_compile
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate

SOURCE = 'VALUE = 1\n'
FORGED = 'VALUE = 2\n'
ENTRY = 'import helper\nprint(helper.VALUE)\n'


def poisoned_module(directory):
    """Ship helper.py returning 1 and a cache entry for it that returns 2."""
    (directory / 'helper.py').write_text(SOURCE, encoding='utf-8')
    (directory / 'entry.py').write_text(ENTRY, encoding='utf-8')
    forged = directory / 'forged.py'
    forged.write_text(FORGED, encoding='utf-8')
    cache = Path(importlib.util.cache_from_source(str(directory / 'helper.py')))
    cache.parent.mkdir()
    # Reproducible-build environments otherwise default to hash-based pycs.
    # This fixture deliberately forges the timestamp/size admission header.
    py_compile.compile(str(forged), cfile=str(cache), doraise=True,
                       invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    state = (directory / 'helper.py').stat()
    payload = bytearray(cache.read_bytes())
    payload[8:12] = struct.pack('<I', int(state.st_mtime) & 0xFFFFFFFF)
    payload[12:16] = struct.pack('<I', state.st_size & 0xFFFFFFFF)
    cache.write_bytes(bytes(payload))
    return cache


class ScorerBytecodeCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.cache = poisoned_module(self.directory)

    def test_the_scorer_reads_the_source_not_the_cache_beside_it(self):
        result = integrate.scoring_subprocess(
            [sys.executable, 'entry.py'], cwd=self.directory,
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('1', result.stdout.strip())

    def test_the_same_cache_is_executed_without_the_redirect(self):
        """Control: without the isolated cache the forged module is what runs."""
        result = subprocess.run(
            [sys.executable, 'entry.py'], cwd=self.directory,
            env=os.environ, capture_output=True, text=True)
        self.assertEqual('2', result.stdout.strip())

    def test_the_scorer_is_started_through_the_isolated_cache(self):
        source = (H / 'integrate.py').read_text(encoding='utf-8')
        launches = [line.strip() for line in source.splitlines() if "str(H / 'score.py')" in line]
        self.assertTrue(launches)
        self.assertEqual([], [line for line in launches if not line.startswith('s = scoring_subprocess(')])


if __name__ == '__main__':
    unittest.main()
