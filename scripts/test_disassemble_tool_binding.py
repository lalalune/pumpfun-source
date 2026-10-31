#!/usr/bin/env python3
"""Disassembly binds executable/input snapshots and refuses their alteration."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / 'disassemble.py'
NAMES = ('pump', 'pump_amm', 'pump_fees', 'mayhem', 'donation_relay')

class DisassembleToolBindingTests(unittest.TestCase):
    def run_fixture(self, mutation=''):
        temporary = tempfile.TemporaryDirectory(prefix='disassemble-binding-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        scripts = root/'scripts';scripts.mkdir()
        (scripts/'disassemble.py').write_bytes(SCRIPT.read_bytes())
        for name in ('deep_disassembly.py', 'window_elf_reader.py'):
            (scripts/name).write_bytes((SCRIPT.parent/name).read_bytes())
        (scripts/'analyze.py').write_text('def program_names(): return '+repr(list(NAMES))+'\n' +
            "def capture_directory(root,name): return root/'evidence'/('dependencies' if name=='donation_relay' else 'original')/name\n")
        for name in NAMES:
            group='dependencies' if name=='donation_relay' else 'original'
            binary=root/f'evidence/{group}/{name}/deployed.so';binary.parent.mkdir(parents=True)
            binary.write_bytes(('original-'+name).encode())
        tool=root/'objdump';out=root/'asm'
        code='#!'+sys.executable+'\nimport pathlib,sys\n'
        code+='original_tool=pathlib.Path('+repr(str(tool))+')\n'
        code+='original_input=pathlib.Path('+repr(str(root/'evidence/original/pump/deployed.so'))+')\n'
        code+="if sys.argv[1]=='--version': print('objdump v1')\nelse:\n"
        code+='    '+(mutation or 'pass').replace('\n','\n    ')+'\n'
        code+="    print(pathlib.Path(sys.argv[-1]).read_text())\n"
        tool.write_text(code);tool.chmod(0o755)
        digest=hashlib.sha256(tool.read_bytes()).hexdigest()
        result=subprocess.run([sys.executable,'-B',str(scripts/'disassemble.py'),
                               '--objdump',str(tool),'--output',str(out)],
                              capture_output=True,text=True,timeout=60)
        return result,root,tool,out,digest

    def test_external_tool_replacement_does_not_change_executed_tool(self):
        result,root,tool,out,digest=self.run_fixture("original_tool.write_text('replacement tool')")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(tool.read_text(),'replacement tool')
        manifest=json.loads((out/'manifest.json').read_text())
        self.assertEqual(manifest['tool_sha256'],digest)
        self.assertEqual(manifest['version'],'objdump v1\n')
        for name in NAMES:
            self.assertEqual((out/f'{name}.asm').read_text(),'original-'+name+'\n')

    def test_external_input_replacement_does_not_change_disassembled_snapshot(self):
        result,root,tool,out,_=self.run_fixture("original_input.write_text('changed input')")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((root/'evidence/original/pump/deployed.so').read_text(),'changed input')
        manifest=json.loads((out/'manifest.json').read_text())
        for name in NAMES:
            self.assertEqual((out/f'{name}.asm').read_text(),'original-'+name+'\n')
            self.assertEqual(manifest['outputs'][name]['input_sha256'],hashlib.sha256(('original-'+name).encode()).hexdigest())

    def test_modified_private_input_is_not_published(self):
        result,root,tool,out,_=self.run_fixture("p=pathlib.Path(sys.argv[-1]); p.chmod(0o644); p.write_text('changed snapshot')")
        self.assertNotEqual(result.returncode,0)
        self.assertIn('snapshot changed during the run',result.stderr)
        self.assertFalse(out.exists())
        self.assertEqual(list(root.glob('.asm.*')),[])

    def test_modified_private_tool_is_not_published(self):
        result,root,tool,out,_=self.run_fixture("p=pathlib.Path(sys.argv[0]); p.chmod(0o755); p.write_text('changed snapshot')")
        self.assertNotEqual(result.returncode,0)
        self.assertIn('snapshot changed during the run',result.stderr)
        self.assertFalse(out.exists())
        self.assertEqual(list(root.glob('.asm.*')),[])

if __name__=='__main__':unittest.main()
