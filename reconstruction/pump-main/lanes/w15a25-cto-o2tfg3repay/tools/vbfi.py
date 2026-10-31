#!/usr/bin/env python3
"""vbfi.py <raw-or-reduced.ll> [edits.py]: BFI of validate at the start of its CGSCC InlinerPass (real -O3 pipeline snapshot),
per to_string site (error line) as freq/entry; C = cold (< 0.02 -> threshold 45). Use on reduce.py output (seconds)."""
import sys,re,os,subprocess,runpy,glob,tempfile
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
CODE2LINE={88:284,83:289,84:296,90:298,89:306,30:307,19:312,91:326,80:330,78:334,77:338}
t=open(sys.argv[1]).read()
if len(sys.argv)>2:
    for e in runpy.run_path(sys.argv[2])['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; assert t.count(x)==1; t=t.replace(x,y)
V=re.search(r'define [^\n]*@(_ZN14pump_recovered9admin_cto8validate17h\w+E)',t).group(1)
d=tempfile.mkdtemp(); p=d+'/in.ll'; open(p,'w').write(t)
r=subprocess.run([OPT,'-O3',p,'-o','/dev/null','-print-before=inline','-print-module-scope','-filter-print-funcs='+V],capture_output=True,text=True)
s=r.stderr; k=s.index('IR Dump Before'); s=s[s.index('\n',k)+1:]; e=s.find('; *** IR Dump',10); s=s[:e] if e>0 else s
open(d+'/snap.ll','w').write(s)
r=subprocess.run([OPT,'-passes=function(print<block-freq>)','-disable-output',d+'/snap.ll'],capture_output=True,text=True)
o=r.stderr; i=o.index('block-frequency-info: '+V); j=o.find('block-frequency-info:',i+10); blk=o[i:j if j>0 else None]
fr={}
for l in blk.split('\n'):
    m=re.match(r'\s*-\s*(\S+): float = (\S+),',l)
    if m: fr[m.group(1)]=float(m.group(2))
vb=s[s.index('define',s.index('@'+V+'(')-600):]; vb=vb[:vb.index('\n}\n')]
cur='start'; code=None; out=[]
for l in vb.split('\n'):
    m=re.match(r'^([\w.$"-]+):',l)
    if m: cur=m.group(1).strip('"')
    m=re.search(r'4from\S*\(i32 noundef (\d+)\)',l)
    if m: code=int(m.group(1))
    if '9to_string' in l and 'call' in l: out.append((CODE2LINE.get(code,code),cur,fr.get(cur,-1)/fr.get('start',1)))
print(' '.join(f'{a}:{f:.4f}{"C" if f<0.02 else ""}' for a,b,f in out))
if os.environ.get('VB_ALL'):
    print(' '.join(f'{b}:{f/fr["start"]:.4f}' for b,f in fr.items()))
if os.environ.get('VB_KEEP'): open(os.environ['VB_KEEP'],'w').write(s)
