#!/usr/bin/env python3
"""oracle.py slim.ll SYM [ops...]: reorder blocks (X>Y moves block X after Y), llc, compare buy vs original. SHOW=1 prints diff."""
import sys,re,subprocess,os,difflib
B=os.path.expanduser('~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin')
D=os.environ.get('ODIR',os.getcwd())
src,sym=sys.argv[1],sys.argv[2]; ops=sys.argv[3:]
ORIG=os.environ.get('ORIG',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-buyv3/oracle/orig.buy.txt'))
def norm(ins):
    ins=re.sub(r'\s*<[^>]*>','',ins).strip()
    ins=re.sub(r'^call .*','call',ins)
    ins=re.sub(r'^(lddw r\d+), .*',r'\1, IMM',ins)
    return ins
lines=open(src).read().split('\n')
s=next(i for i,l in enumerate(lines) if l.startswith('define') and sym in l)
e=next(i for i in range(s,len(lines)) if lines[i]=='}')
body=lines[s+1:e]; blocks=[]; cur=['start',[]]
for l in body:
    m=re.match(r'^([A-Za-z0-9_.]+):',l)
    if m: blocks.append(cur); cur=[m.group(1),[l]]
    else: cur[1].append(l)
blocks.append(cur)
if ops==['list']:
    for n,bl in blocks:
        calls=[re.search(r'@"?([^"( ]+)',x).group(1)[-38:] for x in bl if ' call ' in x and 'lifetime' not in x and '@' in x]
        term=[x.strip()[:70] for x in bl if x.strip().startswith(('br ','switch','ret','unreachable'))]
        print(n,len(bl),term,calls[:2])
    sys.exit()
for op in ops:
    x,y=op.split('>'); bx=next(b for b in blocks if b[0]==x); blocks.remove(bx)
    iy=next(i for i,b in enumerate(blocks) if b[0]==y); blocks.insert(iy+1,bx)
ren=lambda t: re.sub(r'^([0-9]+):', r'v\1:', re.sub(r'%([0-9]+)\b', r'%v\1', t))
out=lines[:s]+[ren(lines[s])]
for n,bl in blocks: out+=[ren(x) for x in bl]
out+=lines[e:]
tag=os.environ.get('TAG','cur'); p=f'{D}/{tag}.ll'; open(p,'w').write('\n'.join(out))
r=subprocess.run([B+'/llc','-O3','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',p,'-o',f'{D}/{tag}.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
fn=re.search(r'@"?([^"( ]*'+sym+r'[^"( ]*)',lines[s]).group(1)
sec=subprocess.run([B+'/llvm-objdump','-d','-j','.text.'+fn,f'{D}/{tag}.o'],capture_output=True,text=True).stdout
C=[norm(l.split('\t')[-1]) for l in sec.split('\n') if re.match(r'^\s*[0-9a-f]+:\t',l)]
O=[norm(l.split(None,1)[1]) for l in open(ORIG) if re.match(r'^0x[0-9a-f]+\s',l)]
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
diff=sum(max(i2-i1,j2-j1) for t,i1,i2,j1,j2 in sm.get_opcodes() if t!='equal')
print(f'orig {len(O)} cand {len(C)} diffslots {diff} ratio {sm.ratio():.4f}')
if os.environ.get('SHOW'):
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t=='equal': print(f'  ={i2-i1}'); continue
        for k in range(i1,i2): print(f'- {k*8:5x} {O[k]}')
        for k in range(j1,j2): print(f'+ {k*8:5x} {C[k]}')
