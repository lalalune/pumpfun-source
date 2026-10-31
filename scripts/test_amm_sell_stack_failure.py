"""A stack-rejected AMM attempt names its overflow in the logged attempt entry."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent / 'amm_sell'
STACK = 'Error: Function example Stack offset of 4104 exceeded max offset of 4096 by 8 bytes.'


def load():
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location('amm_try_sell_under_test', HERE / 'try_sell.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StackFailureEntryTests(unittest.TestCase):
    def test_compiler_success_with_stack_overflow_reports_the_warning(self):
        with tempfile.TemporaryDirectory(prefix='amm-stack-') as directory:
            swarm = Path(directory).resolve()
            with mock.patch.dict(os.environ, {'AMM_SELL_SWARM': str(swarm)}):
                tool = load()
            source = swarm / 'baselines/pristine-ws' / tool.native_build.SELL_REL
            source.parent.mkdir(parents=True)
            source.write_text('// Synthetic source identity only.\n')
            original = swarm / 'infra/original/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(b'Synthetic fixture; never loaded.')

            def build(lane, build_id, **_):
                out = Path(lane) / 'out' / build_id
                out.mkdir(parents=True)
                (out / 'sell.rs').write_text('// Synthetic.\n')
                (out / 'build.log').write_text('   Compiling pump-amm\n' + STACK + '\n    Finished\n')
                (out / 'build-record.json').write_text('{}\n')
                return {'returncode': 1, 'compiler_returncode': 0, 'stack_warnings': [STACK],
                        'seconds': 0.1, 'output_dir': str(out)}

            argv = ['try_sell.py', '--lane', 'fixture', '--approach', 'stack',
                    '--hypothesis', 'Synthetic overflow', '--baseline']
            stdout = io.StringIO()
            with mock.patch.object(tool.native_build, 'build', build), mock.patch.object(sys, 'argv', argv), \
                    contextlib.redirect_stdout(stdout):
                code = tool.main()
            entry = json.loads(stdout.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(entry['status'], 'build_failed')
            self.assertEqual(entry['errors'], [STACK])
            logged = json.loads((swarm / 'ATTEMPTS.jsonl').read_text())
            self.assertEqual(logged['errors'], [STACK])


if __name__ == '__main__':
    unittest.main()
