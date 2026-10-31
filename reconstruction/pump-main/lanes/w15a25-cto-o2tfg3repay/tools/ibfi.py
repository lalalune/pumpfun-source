#!/usr/bin/env python3
"""ibfi.py <raw.ll> [edits.py]: inline-time BFI of validate's to_string call sites. Snapshot the module right before
validate's CGSCC InlinerPass (-print-before=inline -print-module-scope), make to_string noinline, run cgscc(inline) on the
snapshot (inlines eq/name/from/... as the real worklist does), then print<block-freq> of validate: freq/entry per site.
Cold-callsite rule: < 0.02 -> threshold 45 -> outlined."""
import sys,re,os,subprocess,runpy,glob,tempfile
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
CODE2LINE={88:284,83:289,84:296,90:298,89:306,30:307,19:312,91:326,80:330,78:334,77:338}
TS='_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h1551814bef63e52cE'
def run(t):
    V=re.search(r'define [^\n]*@(_ZN14pump_recovered9admin_cto8validate17h\w+E)',t).group(1)
    d=tempfile.mkdtemp(); p=d+'/in.ll'; open(p,'w').write(t)
    r=subprocess.run([OPT,'-O3',p,'-o','/dev/null','-print-before=inline','-print-module-scope','-filter-print-funcs='+V],capture_output=True,text=True)
    s=r.stderr; s=s[s.index('\n',s.index('IR Dump Before'))+1:]
    # make to_string noinline
    m=re.search(r'(define internal [^\n]*@"'+re.escape(TS)+r'"\([^\n]*\)[^\n]*?)#(\d+)',s)
    s=s.replace(m.group(0),m.group(1)+'#9002',1)+'\nattributes #9002 = { noinline }\n'
    # keep validate alive: its call sites in execute become noinline
    s=re.sub(r'(call [^\n]*@'+V+r'\([^\n]*\))( #\d+)?\n',lambda q:q.group(1)+' #9002\n',s)
    open(d+'/snap.ll','w').write(s)
    r=subprocess.run([OPT,'-passes='+os.environ.get('IB_PASSES','cgscc(inline),function(print<block-freq>)'),d+'/snap.ll','-o',d+'/o.ll','-S'],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
    if os.environ.get('IB_KEEP'): open(os.environ['IB_KEEP'],'w').write(r.stderr); subprocess.run(['cp',d+'/o.ll',os.environ['IB_KEEP']+'.ll'])
    # parse freq of validate blocks
    out=r.stderr; i=out.index("block-frequency-info: "+V); j=out.find('block-frequency-info:',i+10); blk=out[i:j if j>0 else None]
    fr={}
    for l in blk.split('\n'):
        m=re.match(r'\s*-\s*(\S+): float = (\S+),',l)
        if m: fr[m.group(1)]=float(m.group(2))
    o=open(d+'/o.ll').read(); k=o.index('define',o.index('@'+V)-400); body=o[k:o.index('\n}\n',k)]
    # alloc constant (to_string self arg) -> error code, from the snapshot's validate body
    a2c={}; vb=s[s.index('define',s.index('@'+V)-400):]; vb=vb[:vb.index('\n}\n')]; last=None
    for l in vb.split('\n'):
        m=re.search(r'4from\S*\(i32 noundef (\d+)\)',l)
        if m: last=int(m.group(1))
        m=re.search(r'@"?'+re.escape(TS)+r'"?\(.*?(@alloc_\w+)',l)
        if m and 'call' in l: a2c[m.group(1)]=last
    cur='start'; res=[]
    for l in body.split('\n'):
        m=re.match(r'^([\w.$"-]+):',l)
        if m: cur=m.group(1).strip('"')
        m=re.search(r'@"?'+re.escape(TS)+r'"?\(.*?(@alloc_\w+)',l)
        if m and 'call' in l: res.append([cur,a2c.get(m.group(1))])
    ent=fr.get('start',1.0)
    return [(CODE2LINE.get(c,c),b,fr.get(b,-1)/ent) for b,c in res]
if __name__=='__main__':
    t=open(sys.argv[1]).read()
    if len(sys.argv)>2:
        for e in runpy.run_path(sys.argv[2])['EDITS']:
            if callable(e): t=e(t); continue
            x,y=e; assert t.count(x)==1; t=t.replace(x,y)
    print(' '.join(f'{l}:{f:.4f}{"C" if f<0.02 else ""}' for l,b,f in run(t)))
