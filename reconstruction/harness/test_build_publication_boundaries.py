from pathlib import Path
import json
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import fastbuild as F
import link_order as L

class PublicationBoundaryTests(unittest.TestCase):
    def test_different_workspaces_cannot_publish_to_the_same_output(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);entered=threading.Event();release=threading.Event();errors=[]
            def build(src,work,out,**kw):
                out.mkdir(parents=True,exist_ok=True);(out/'receipt').write_text(work.name)
                if work.name=='first':entered.set();release.wait(5)
                return {'ok':True}
            def first():
                try:F.build(r/'source',r/'first',r/'out')
                except Exception as e:errors.append(e)
            with patch.object(F,'_build_locked',side_effect=build):
                thread=threading.Thread(target=first);thread.start();self.assertTrue(entered.wait(5))
                try:
                    with self.assertRaisesRegex(RuntimeError,'output.*in use'):
                        F.build(r/'source',r/'second',r/'out')
                    self.assertEqual((r/'out/receipt').read_text(),'first')
                    self.assertTrue(F.build(r/'source',r/'independent',r/'other-output')['ok'])
                finally:release.set();thread.join(5)
                self.assertEqual(errors,[]);self.assertTrue(F.build(r/'source',r/'second',r/'out')['ok'])

    def test_stripping_failure_leaves_no_current_binaries(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);src=r/'src';src.mkdir();work=r/'work';out=r/'out';out.mkdir()
            (out/'candidate.so').write_bytes(b'prior stripped');(out/'unstripped.so').write_bytes(b'prior full')
            crate=work/'ws/programs/pump';crate.mkdir(parents=True);(crate/'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
            recipe={'triple':'sbpf-solana-solana','rustc':r/'rustc','template':r/'absent'}
            def compile(*args,**kw):
                built=work/'target-identity'/recipe['triple']/'release/fixture.so';built.parent.mkdir(parents=True);built.write_bytes(b'compiled')
                return subprocess.CompletedProcess([],0,'Finished'),False
            def strip(command,**kw):
                Path(command[-1]).write_bytes(b'incomplete stripping')
                raise subprocess.CalledProcessError(2,command,stderr='strip failed')
            with patch.object(F,'RECIPES',{'identity':recipe}),patch.object(F,'stage',return_value=crate),patch.object(F,'acquire_slot') as slot,patch.object(F,'run_compiler',side_effect=compile),patch.object(F.subprocess,'run',side_effect=strip):
                with self.assertRaises(subprocess.CalledProcessError):F.build(src,work,out)
            self.assertFalse((out/'unstripped.so').exists());self.assertFalse((out/'candidate.so').exists())
            self.assertTrue((out/'build.log').exists());self.assertEqual(len(list((out/'previous').iterdir())),1)
            with F.workspace_lock(work):pass

    def test_linker_consumes_a_snapshot_of_the_validated_script(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);script=r/'ordered.ld';original=L.DEFAULT.read_bytes();script.write_bytes(original)
            incoming=r/'default.ld';incoming.write_bytes(original);receipt=r/'receipt.json';linker=r/'lld';linker.write_bytes(b'fixture')
            env={'PUMP_LINK_SCRIPT':str(script),'PUMP_LINK_SCRIPT_SHA256':L.sha(script),'PUMP_LINK_LLD':str(linker),'PUMP_LINK_RECEIPT':str(receipt)}
            consumed=[]
            def invoke(executable,args):
                script.write_bytes(b'unadmitted replacement')
                consumed.append(Path(args[args.index('--script')+1]).read_bytes())
            def run(args,**kw):invoke(args[0],args);return subprocess.CompletedProcess(args,0)
            with patch.object(L.os,'execv',side_effect=invoke),patch.object(L,'subprocess',create=True) as process:
                process.run.side_effect=run
                L.lld_main(['hook','--script',str(incoming)],env)
            self.assertEqual(consumed,[original])
            self.assertEqual(json.loads(receipt.read_text())['script_sha256'],__import__('hashlib').sha256(consumed[0]).hexdigest())
if __name__=='__main__':unittest.main()
