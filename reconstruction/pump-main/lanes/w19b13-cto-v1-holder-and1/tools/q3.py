import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from po import *
import fx
VAL='admin_cto8validate'; EXE='admin_cto7execute17'
base=open(OUT+'/ir/'+os.environ.get('QBASE','s2')+'.s.ll').read()
def fnsub(t,name,f):
    m=re.search(r'^define [^\n]*'+name+r'[^\n]*\{\n',t,re.M); e=t.index('\n}\n',m.end())+3
    return t[:m.start()]+f(t[m.start():e])+t[e:]
PV="  %%pv%d = load volatile i8, ptr %%holder_key, align 1\n"
def padv(block,n=1,idx=0):
    def f(b):
        a=re.search(r'^'+re.escape(block)+r':[^\n]*\n',b,re.M); assert a,block
        return b[:a.end()]+''.join(PV%(idx+i) for i in range(n))+b[a.end():]
    return lambda t:fnsub(t,VAL,f)
def pade(block,n=1,idx=0,ptr='%hkx'):
    PE="  %%pe%d = load volatile i8, ptr "+ptr+", align 1\n"
    def f(b):
        a=re.search(r'^'+re.escape(block)+r':[^\n]*\n',b,re.M); assert a,block
        return b[:a.end()]+''.join(PE%(idx+i) for i in range(n))+b[a.end():]
    return lambda t:fnsub(t,EXE,f)
def run(name,fs,ref='m1'):
    t=base
    for f in fs: t=f(t)
    r=fx.run(t,name,keep=False)
    if 'err' in r: print(json.dumps(r)[:600],flush=True); return r
    q=subprocess.run(['python3',T+'/rg.py',f'{OUT}/fx/{name}/fn.bin',f'{OUT}/fx/{ref}/fn.bin'],capture_output=True,text=True)
    r['rg']=q.stdout.strip(); print(json.dumps(r)[:480],flush=True); return r
if __name__=='__main__':
    run('r0',[])
    run('r1',[padv('bb7')])
    run('r2',[padv('bb7'),pade('bb24',3)])
    run('r3',[padv('bb7'),pade('bb25',3)])
