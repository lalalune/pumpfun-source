import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from po import *
import fx
base=open(OUT+'/ir/m0.s.ll').read()
def run(name,f,ref='m0'):
    t=f(base)
    r=fx.run(t,name,keep=False)
    if 'err' in r: print(json.dumps(r)[:800],flush=True); return r
    q=subprocess.run(['python3',T+'/rg.py',f'{OUT}/fx/{name}/fn.bin',f'{OUT}/fx/{ref}/fn.bin'],capture_output=True,text=True)
    r['rg']=q.stdout.strip()
    print(json.dumps(r)[:800],flush=True)
    return r
PT='%%tp%d = call noundef ptr @llvm.bpf.passthrough.p0.p0(i32 noundef zeroext %d, ptr noundef nonnull %s)\n'
def t307(t):
    a="  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_87, ptr align 1 %t, i64 32, i1 false)\n"
    return rep(t,a,'  '+PT%(1,77,'%t')+"  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_87, ptr align 1 %tp1, i64 32, i1 false)\n")
if __name__=='__main__':
    run('q_t307',t307)
