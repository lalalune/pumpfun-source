#!/usr/bin/env python3
"""coal.py <m.ll> [force]: run llc to the end of the register coalescer and report whether the swept payload (event field
store at +184 of the event buffer) and the return block's Result payload phi (store at +8 of the sret pointer before EXIT)
are one vreg (the original's r9 class). Also prints the preds of the block holding a 'RP = COPY SW' copy. Experiment only."""
import sys,os,re,subprocess
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9')
LLC=OUT+'/llvmb/bin/llc'
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
m=sys.argv[1]; o=m+'.coal.mir'
r=subprocess.run([LLC,*A,m,'-stop-after=register-coalescer','-o',o],capture_output=True,text=True)
if r.returncode: sys.exit(r.stderr[-500:])
t=open(o).read(); os.remove(o)
body=t[t.index('body:'):]
blocks=re.split(r'\n  (bb\.\d+[^\n]*):\n',body)
B={}; order=[]
for i in range(1,len(blocks),2):
    hdr=blocks[i]; txt=blocks[i+1]; n=int(re.match(r'bb\.(\d+)',hdr).group(1)); B[n]=(hdr,txt); order.append(n)
sw=None; rp=None
for n in order:
    hdr,txt=B[n]
    for mm in re.finditer(r'STD_V1 (?:killed )?%(\d+), %stack\.\d+\._41\.i, 184\b',txt): sw=mm.group(1)
    if 'EXIT' in txt:
        mm=re.search(r'STD_V1 (?:killed )?%(\d+), (?:killed )?%\d+, 8 ',txt)
        if mm: rp=mm.group(1)
preds={}
for n in order:
    hdr,txt=B[n]
    for s in re.findall(r'successors: ([^\n]*)',txt):
        for x in re.findall(r'%bb\.(\d+)',s): preds.setdefault(int(x),set()).add(n)
cp=[]
for n in order:
    hdr,txt=B[n]
    for mm in re.finditer(r'%'+str(rp)+r':gpr = COPY (?:killed )?%(\d+)',txt): cp.append((n,mm.group(1),len(preds.get(n,())),len(set(re.findall(r'%bb\.(\d+)',(re.findall(r'successors: ([^\n]*)',txt) or [''])[0])))))
print('SW=%%%s RP=%%%s merged=%s'%(sw,rp,sw==rp))
for n,src,np,ns in cp: print('  RP=COPY %%%s in bb.%d (preds %d, succs %d)%s'%(src,n,np,ns,'  <- SW' if src==sw else ''))
