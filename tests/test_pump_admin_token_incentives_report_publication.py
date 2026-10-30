"""Real CLI/VM controls for publishing admin incentive reports.

Build JSON in this test is explicitly synthetic hash-admission metadata. The
candidate is a captured ELF; no source rebuild or whole-program proof is claimed.
Each publication run uses two retained cases, while the existing image-pinning
suite keeps its full variant coverage.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/pump_admin_token_incentives_differential.py'
SOURCES = ('programs/pump/src/incentives.rs', 'programs/pump/src/volume_sync.rs',
           'programs/pump/src/lib.rs', 'programs/pump/Cargo.toml', 'programs/pump/Cargo.lock')
DEPENDENCIES = ('spl_token', 'spl_token_2022', 'associated_token')
DRIVER = r'''
import gzip, json, os, runpy, sys
from pathlib import Path
scripts, directory, mode, destination = sys.argv[1:]
sys.path.insert(0, scripts)
import pump_differential_output as publication
root = Path(directory); output = Path(destination); completed = []
def decode(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
if mode == 'fsync-failure':
    def fail(fd): raise OSError('injected fsync failure')
    publication.os.fsync = fail
elif mode in ('atomic-replace', 'recreated-stage'):
    replace = publication.os.replace
    def publish(stage, dest):
        assert decode(stage)['summary']['cases'] == 2
        assert Path(dest).read_bytes() == b'prior complete receipt'
        replace(stage, dest)
        if mode == 'recreated-stage':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated.txt').write_text(str(stage))
    publication.os.replace = publish
script = str(Path(scripts)/'pump_admin_token_incentives_differential.py')
def hook(frame, event, arg):
    if frame.f_code.co_filename != script: return
    if event == 'call' and frame.f_code.co_name == 'main':
        g=frame.f_globals; g['ROOT']=root;g['TARGET']=root/'original.so'
        g['IDL']=root/'idl.json';g['SNAPSHOT']=root/'snapshot.json'
        g['DEPENDENCIES']={name:root/(name+'.so') for name in ('spl_token','spl_token_2022','associated_token')}
        selected=g['variants']()[:2];g['variants']=lambda:selected
    if event == 'return' and frame.f_code.co_name == 'run':
        completed.append(1)
        if len(completed)==2 and mode=='late-alias':
            os.link(root/'build.json',output)
sys.argv=[script,'--candidate',str(root/'candidate.so'),'--build-comparison',str(root/'build.json'),
          '--second-build-comparison',str(root/'second.json'),'--output',str(output)]
sys.setprofile(hook)
try:
    runpy.run_path(script,run_name='__main__')
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(completed))
'''


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


class AdminIncentivePublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='admin-incentive-publication-')
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name).resolve()
        for name in ('original.so','candidate.so'):
            shutil.copyfile(ROOT/'evidence/original/pump/deployed.so',self.root/name)
        shutil.copyfile(ROOT/'evidence/upstream/pump.json',self.root/'idl.json')
        shutil.copyfile(ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json',self.root/'snapshot.json')
        for name in DEPENDENCIES:
            shutil.copyfile(ROOT/f'evidence/dependencies/{name}/deployed.so',self.root/(name+'.so'))
        for name in SOURCES:
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        self.write_bindings()
        self.input_bytes={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.output=self.root/'reports/output.json.gz'

    def write_bindings(self):
        binding={'test_only':'synthetic hash admission; no rebuild evidence',
                 'comparison':{'original_sha256':sha(self.root/'original.so'),
                               'candidate_sha256':sha(self.root/'candidate.so')},
                 'source_sha256':{'test_only':'no compilation claimed'},'selected_toolchain':'v1.44'}
        for name in ('build.json','second.json'):
            (self.root/name).write_text(json.dumps(binding))

    def invoke(self,mode='normal',output=None):
        env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B','-c',DRIVER,str(ROOT/'scripts'),str(self.root),mode,
            str(output or self.output)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)

    def executions(self):return len(json.loads((self.root/'executions.json').read_bytes()))

    def report(self,path=None):
        raw=(path or self.output).read_bytes()
        return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)

    def test_real_cli_supports_complete_json_and_gzip(self):
        for suffix in ('json','json.gz'):
            path=self.output.with_name('report.'+suffix)
            result=self.invoke(output=path)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            report=self.report(path)
            self.assertEqual(report['summary']['cases'],2)
            self.assertEqual(report['summary']['matched'],2)
            self.assertEqual(self.executions(),4)
            self.assertTrue(all(row['target']['signature_verified'] and row['candidate']['signature_verified']
                                for row in report['cases']))
            self.assertTrue(any(row['target']['events'] for row in report['cases']))

    def test_candidate_builds_and_source_aliases_rejected_before_execution(self):
        for name in ('candidate.so','original.so','build.json','second.json','idl.json','snapshot.json',
                     'spl_token.so',SOURCES[0]):
            source=self.root/name;before=source.read_bytes()
            for kind in ('direct','symlink','hardlink'):
                with self.subTest(name=name,kind=kind):
                    # Unsafe implementations may clobber inputs in the prior subtest.
                    for path,raw in self.input_bytes.items():path.write_bytes(raw)
                    destination=source if kind=='direct' else self.root/(Path(name).name+'-'+kind)
                    if kind=='symlink':destination.symlink_to(source)
                    if kind=='hardlink':os.link(source,destination)
                    result=self.invoke(output=destination)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('report output aliases an input',result.stderr)
                    self.assertEqual(self.executions(),0)
                    self.assertEqual(source.read_bytes(),before)

    def test_late_build_alias_is_rejected_and_preserved(self):
        self.output.parent.mkdir();before=(self.root/'build.json').read_bytes()
        result=self.invoke('late-alias')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('report output aliases an input',result.stderr)
        self.assertEqual(self.executions(),4)
        self.assertEqual((self.root/'build.json').read_bytes(),before)
        self.assertTrue(self.output.samefile(self.root/'build.json'))

    def test_fsync_failure_preserves_existing_report(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior complete receipt')
        result=self.invoke('fsync-failure')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('injected fsync failure',result.stderr)
        self.assertEqual(self.executions(),4)
        self.assertEqual(self.output.read_bytes(),b'prior complete receipt')
        self.assertEqual(list(self.output.parent.iterdir()),[self.output])

    def test_atomic_replace_publishes_complete_report(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior complete receipt')
        result=self.invoke('atomic-replace')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.report()['summary']['matched'],2)
        self.assertEqual(list(self.output.parent.iterdir()),[self.output])

    def test_recreated_consumed_stage_remains_owned_by_later_writer(self):
        self.output.parent.mkdir();self.output.write_bytes(b'prior complete receipt')
        result=self.invoke('recreated-stage')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        path=Path((self.root/'recreated.txt').read_text())
        self.assertEqual(path.read_bytes(),b'new staging owner')
        self.assertEqual(self.report()['summary']['matched'],2)

    def test_wrong_real_image_publishes_mismatches_and_exits_one(self):
        shutil.copyfile(ROOT/'evidence/original/pump_fees/deployed.so',self.root/'candidate.so')
        self.write_bindings()
        result=self.invoke()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        report=self.report();self.assertEqual(report['summary']['cases'],2)
        self.assertLess(report['summary']['matched'],2)
        self.assertEqual(self.executions(),4)


if __name__=='__main__':unittest.main()
