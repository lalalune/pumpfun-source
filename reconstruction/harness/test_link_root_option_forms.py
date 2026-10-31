import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import link_order


class RootOptionForms(unittest.TestCase):
    def test_real_wrapper_routes_equal_and_comma_forms(self):
        forms = [
            ['--crate-name=pump_recovered', '--crate-type=cdylib'],
            ['--crate-name', 'pump_recovered', '--crate-type', 'rlib,cdylib'],
            ['--crate-name=pump_recovered', '--crate-type=rlib,cdylib'],
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / 'argv.json'
            following = root / 'next_wrapper.py'
            following.write_text('import json,os,sys\nfrom pathlib import Path\nPath(os.environ["TEST_ARGV"]).write_text(json.dumps(sys.argv[1:]))\n', encoding='utf-8')
            env = dict(os.environ, PUMP_LINK_ROOT_CRATE='pump_recovered', PUMP_LINK_NEXT_WRAPPER=str(following), TEST_ARGV=str(receipt))
            for options in forms:
                with self.subTest(options=options):
                    result = subprocess.run([sys.executable, str(link_order.H / 'pump_link_rustc.py'), 'compiler-not-executed', *options], env=env, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    forwarded = json.loads(receipt.read_text())
                    self.assertEqual(forwarded[:-2], ['compiler-not-executed', *options])
                    self.assertEqual(forwarded[-2:], ['-C', 'linker=' + str(link_order.H / 'pump_link_lld.sh')])

    def test_every_codegen_linker_form_is_rejected_for_the_root(self):
        env = {'PUMP_LINK_ROOT_CRATE': 'pump', 'PUMP_LINK_NEXT_WRAPPER': 'next'}
        prefix = ['wrapper', 'rustc', '--crate-name', 'pump', '--crate-type', 'cdylib']
        for option in (['-C', 'linker=other'], ['-Clinker=other'], ['--codegen', 'linker=other'], ['--codegen=linker=other']):
            with self.subTest(option=option):
                with self.assertRaisesRegex(ValueError, 'already sets a linker'):
                    link_order.rustc_args([*prefix, *option], env)

    def test_option_terminator_keeps_positional_arguments_unchanged(self):
        env = {'PUMP_LINK_ROOT_CRATE': 'pump', 'PUMP_LINK_NEXT_WRAPPER': 'next'}
        args = ['--', '--crate-name=pump', '--crate-type=cdylib']
        self.assertEqual(link_order.rustc_args(['wrapper', 'rustc', *args], env)[3:], args)

    def test_root_hook_is_inserted_before_the_option_terminator(self):
        env = {'PUMP_LINK_ROOT_CRATE': 'pump', 'PUMP_LINK_NEXT_WRAPPER': 'next'}
        options = ['--crate-name', 'pump', '--crate-type', 'cdylib']
        command = link_order.rustc_args(['wrapper', 'rustc', *options, '--', 'source.rs'], env)
        self.assertEqual(command[3:], [*options, '-C', 'linker=' + str(link_order.H / 'pump_link_lld.sh'), '--', 'source.rs'])


if __name__ == '__main__': unittest.main()
