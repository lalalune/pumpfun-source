"""Replay actual images and reject isolated synthetic data/reference fixtures."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
if not __debug__:
    raise SystemExit('Run the test driver without -O; it separately tests the verifier with -O.')
import argparse
ap=argparse.ArgumentParser(description=__doc__)
for name in ['control','candidate','original','inventory','harness','work']:
    ap.add_argument('--'+name,type=Path,required=True)
args=ap.parse_args()
D=args.work.resolve();D.mkdir(parents=True,exist_ok=False)
H=args.harness.resolve();control=args.control.resolve();candidate=args.candidate.resolve()
sys.path.insert(0,str(H));import score
score.BASE=D/'base';score.BASE.mkdir()
(score.BASE/'original.so').write_bytes(args.original.read_bytes())
(score.BASE/'functions.tsv').write_bytes(args.inventory.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
raw=candidate.read_bytes();sec=score.sections(raw);baseline,_=score.score_with_hash(candidate)
common=['--control',str(control),'--original',str(args.original.resolve()),'--inventory',str(args.inventory.resolve()),'--harness',str(H)]
rows={}
def run(label,path,opts=[],expect=None):
    cmd=[sys.executable,'-I','-B',*opts,str(Path(__file__).resolve().with_name('verify_relocations.py')),*common,'--candidate',str(path),'--work',str(D/('check-'+label))]
    r=subprocess.run(cmd,capture_output=True)
    (D/(label+'.stdout.log')).write_bytes(r.stdout);(D/(label+'.stderr.log')).write_bytes(r.stderr)
    assert (r.returncode==0) if expect is None else (r.returncode!=0 and expect in r.stderr.decode())
    rows[label]={'returncode':r.returncode,'expected_rejection':expect,'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr)}
run('normal',candidate);run('optimized',candidate,['-O'])
assert (D/'check-normal/verification.json').read_bytes()==(D/'check-optimized/verification.json').read_bytes()
N=D/'negative-fixtures';N.mkdir()
for label in ['scalar','data-target','lddw-target']:
    b=bytearray(raw)
    if label=='scalar':
        pos=sec['.data.rel.ro']['offset']+8;b[pos]^=1;expected='Non-relocation data bytes changed'
    elif label=='data-target':
        pos=sec['.data.rel.ro']['offset']+4;value=struct.unpack_from('<I',b,pos)[0];struct.pack_into('<I',b,pos,value+1);expected='Data target offset changed'
    else:
        f=[f for f in score.candidate_functions(candidate) if '14pump_recovered7sell_v217h' in f[2]];assert len(f)==1
        start,size,_=f[0];body=score.body(raw,sec,start,size);i=0
        while i<len(body):
            if body[i]==0x18:
                value=struct.unpack_from('<I',body,i+4)[0]|struct.unpack_from('<I',body,i+12)[0]<<32
                if sec['.rodata']['addr']<=value<sec['.rodata']['addr']+sec['.rodata']['size']-1:break
                i+=16
            else:i+=8
        assert i<len(body)
        pos=sec['.text']['offset']+start-sec['.text']['addr']+i+4
        struct.pack_into('<I',b,pos,value+1);expected='Retained body class data references changed'
    path=N/(label+'.synthetic.so');path.write_bytes(b)
    measured,digest=score.score_with_hash(path)
    assert set(measured)==set(baseline) and all(measured[k][field]==baseline[k][field] for k in baseline for field in ['normalized','raw'])
    run(label,path,expect=expected)
    rows[label].update(fixture_sha256=digest,changed_file_offset=pos,all_1035_memberships_unchanged=True,
                       scope='Synthetic negative test fixture only; never a compiler output, reconstruction candidate or executed program.')
assert candidate.read_bytes()==raw
save(D/'validation.json',{'result':'PASS','cases':rows,'actual_inputs_unchanged':True,'compiler_or_target_runs_in_validation':0})
print(json.dumps({'result':'PASS','cases':rows},indent=2))
