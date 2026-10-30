"""sroa.py [edit.py]: apply edit to pre-SROA module m1c.ll (execute body only), run LLVM18 opt sroa, print _84 phi order in the validate exit block."""
import sys,subprocess,re,os,runpy
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb-cv2/ir/presroa')
OPT='/Users/shawwalters/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt'
H='define hidden { i64, ptr } @_ZN14pump_recovered9create_v27execute'
def get():
    t=open(D+'/m1c.ll').read(); i=t.index(H); j=t.index('\n}\n',i)+3; return t,i,j
def run(t2,tag='x'):
    p=D+f'/e_{tag}.ll'; open(p,'w').write(t2)
    r=subprocess.run([OPT,'-S','-passes=function(sroa<modify-cfg>)',p,'-o',D+f'/o_{tag}.ll'],capture_output=True,text=True)
    if r.returncode: return 'ERR '+r.stderr[-400:]
    o=open(D+f'/o_{tag}.ll').read(); i=o.index(H); e=o[i:o.index('\n}\n',i)]
    out=[]
    for m in re.finditer(r'\n([\w.$"]+):[^\n]*\n((?:  %[^\n]*= phi[^\n]*\n)+)',e):
        ph=re.findall(r'%(_84\.sroa\.\d+)',m.group(2))
        names=re.findall(r'  %(_84\.sroa\.\d+)[\w.]* = phi',m.group(2))
        if len(names)>=3: out.append(m.group(1)[:50]+': '+','.join(n.split('.')[-1] for n in names))
    return '; '.join(out)
if __name__=='__main__':
    t,i,j=get()
    if len(sys.argv)>1: f=t[i:j]; f2=runpy.run_path(sys.argv[1])['edit'](f); assert f2!=f; t=t[:i]+f2+t[j:]
    print(run(t))
