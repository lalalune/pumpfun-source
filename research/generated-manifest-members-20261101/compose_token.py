import argparse, difflib, hashlib, json
from pathlib import Path
import subprocess, sys, tempfile
BASE = '60a42309a4908577f0a386513eeaee6cd6f84f42'
TOKEN = '492a9d7da5614d0f7f87e9d789bbf9efe0d89179'
NAME = 'scripts/bytecode_signatures.py'
def sha(b): return hashlib.sha256(b).hexdigest()
p = argparse.ArgumentParser(); p.add_argument('root',type=Path); p.add_argument('--output',type=Path,required=True); args=p.parse_args()
root=args.root.resolve()
def show(rev,name): return subprocess.check_output(['git','-C',str(root),'show',rev+':'+name])
base=show(BASE,NAME); fixed=(root/NAME).read_bytes(); token=show(TOKEN,NAME)
# Review enforces this patch is only the emitted verifier template transition.
patch=''.join(difflib.unified_diff(base.decode().splitlines(True),fixed.decode().splitlines(True),fromfile='a/'+NAME,tofile='b/'+NAME)).encode()
assert b'def manifest_members(pairs)' in patch
sources={n:show(TOKEN,n) for n in (NAME,'scripts/deep_disassembly.py','scripts/analyze.py','scripts/window_elf_reader.py')}
evidence={p.relative_to(root).as_posix():p.read_bytes() for p in (root/'evidence').rglob('*') if p.is_file()}
results=[]
with tempfile.TemporaryDirectory(prefix='manifest-token-composition-') as t:
    temp=Path(t); src=temp/'source'; src.mkdir()
    for n,b in {**sources,**evidence}.items():
        path=src/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    for kind in ('token_only','token_plus_manifest'):
        if kind=='token_plus_manifest':
            subprocess.run(['git','apply','--check','-'],input=patch,cwd=src,check=True)
            subprocess.run(['git','apply','-'],input=patch,cwd=src,check=True)
        out=temp/kind
        run=subprocess.run([sys.executable,'-I','-B',str(src/NAME),'--output',str(out)],capture_output=True,text=True,cwd=src)
        assert run.returncode==0,run.stderr
        source_sha=sha((src/NAME).read_bytes())
        files={f.name:sha(f.read_bytes()) for f in out.iterdir()}
        manifest=(out/'manifest.json').read_bytes()
        rows=[]
        for case,data in [('clean',manifest),('duplicate',b'{"summary.json":"'+b'0'*64+b'",'+manifest.lstrip()[1:])]:
            (out/'manifest.json').write_bytes(data)
            codes=[]
            for mode in ([],['-O'],['-OO']):
                check=subprocess.run([sys.executable,'-I','-B',*mode,str(out/'verify.py')],capture_output=True,text=True,cwd=out)
                expected=1 if kind=='token_plus_manifest' and case=='duplicate' else 0
                assert check.returncode==expected,(kind,case,check.stdout,check.stderr)
                codes.append(check.returncode)
            rows.append({'case':case,'normal_O_OO_exit':codes})
        (out/'manifest.json').write_bytes(manifest)
        assert files=={f.name:sha(f.read_bytes()) for f in out.iterdir()}
        del files['manifest.json'],files['verify.py']
        results.append({'cohort':kind,'signature_source_sha256':source_sha,'analysis_payload_sha256':files,'verifiers':rows})
    assert results[0]['analysis_payload_sha256']==results[1]['analysis_payload_sha256']
    assert all((src/n).read_bytes()==b for n,b in evidence.items())
assert all((root/n).read_bytes()==b for n,b in evidence.items())
assert (root/NAME).read_bytes()==fixed
result={'base':BASE,'token_pr':'https://github.com/lalalune/pumpfun-source/pull/3920','token_head':TOKEN,'template_patch_sha256':sha(patch),'actual_generator_calls':2,'actual_verifier_calls':12,'same_ten_analysis_payloads':True,'inputs_unchanged':True,'results':results}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'}))
