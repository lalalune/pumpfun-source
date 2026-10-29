#!/usr/bin/env python3
"""irx.py slim.ll edit.py [tag]: apply edit(text)->text, llc, compare sell vs original (SHOW=1 for diff)."""
import sys,re,subprocess,os,difflib,runpy
B=os.path.expanduser('~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin')
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi/oracle')
src,ed=sys.argv[1],sys.argv[2]; tag=sys.argv[3] if len(sys.argv)>3 else 'x'
sym=os.environ.get('SYM','_ZN14pump_recovered5trade4sell17h')
ORIG=os.environ.get('ORIG',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi/orig.txt'))
def norm(ins):
    ins=re.sub(r'\s*<[^>]*>','',ins).strip()
    ins=re.sub(r'^call .*','call',ins)
    ins=re.sub(r'^(lddw r\d+), .*',r'\1, IMM',ins)
    return ins
t=open(src).read()
if ed!='-':
    t2=runpy.run_path(ed)['edit'](t); assert t2!=t,'edit changed nothing'; t=t2
p=f'{D}/{tag}.ll'; open(p,'w').write(t)
r=subprocess.run([B+'/llc','-O3','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',p,'-o',f'{D}/{tag}.o']+os.environ.get('LLCX','').split(),capture_output=True,text=True)
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
fn=re.search(r'^define[^@]*@"?([^"( ]*'+sym+r'[^"( ]*)',t,re.M).group(1)
sec=subprocess.run([B+'/llvm-objdump','-d','-j','.text.'+fn,f'{D}/{tag}.o'],capture_output=True,text=True).stdout
C=[norm(l.split('\t')[-1]) for l in sec.split('\n') if re.match(r'^\s*[0-9a-f]+:\t',l)]
O=[norm(l.split(None,1)[1]) for l in open(ORIG) if re.match(r'^0x[0-9a-f]+\s',l)]
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
diff=sum(max(i2-i1,j2-j1) for t_,i1,i2,j1,j2 in sm.get_opcodes() if t_!='equal')
print(f'{tag}: orig {len(O)} cand {len(C)} diffslots {diff} ratio {sm.ratio():.4f} exact={O==C}')
if os.environ.get('SHOW'):
    for t_,i1,i2,j1,j2 in sm.get_opcodes():
        if t_=='equal': print(f'  ={i2-i1}'); continue
        for k in range(i1,i2): print(f'- {k*8:5x} {O[k]}')
        for k in range(j1,j2): print(f'+ {k*8:5x} {C[k]}')
