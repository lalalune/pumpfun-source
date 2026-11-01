#!/usr/bin/env python3
"""vcomb.py <base m.ll> <out.jsonl> <spec>...: apply a set of volatile edits (Lline = load at line, Sline = store at line) and llc+score.
Prints one JSON line per spec set. Spec set is comma-separated, e.g. L4320,S5000"""
import sys,os,re,subprocess,json,tempfile
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,outf=sys.argv[1],sys.argv[2]; sets=sys.argv[3:]
L=open(base).read().split('\n'); orig=oracle.orig_window()
def ed(T,s):
    k,i=s[0],int(s[1:])-1; l=T[i]
    if k=='L':
        m=re.match(r'^(\s*%[\w.$"]+ = )load (?!volatile)(.*)$',l); assert m,(s,l); T[i]=m.group(1)+'load volatile '+m.group(2)
    elif k=='M':
        assert l.rstrip().endswith('i1 false)'),(s,l); T[i]=l.rstrip()[:-len('i1 false)')]+'i1 true)'
    else:
        m=re.match(r'^(\s*)store (?!volatile)(.*)$',l); assert m,(s,l); T[i]=m.group(1)+'store volatile '+m.group(2)
for st in sets:
    T=L[:]
    for s in st.split(','):
        if s: ed(T,s)
    d=tempfile.mkdtemp(prefix='vc',dir=os.path.dirname(os.path.abspath(outf)))
    open(d+'/m.ll','w').write('\n'.join(T))
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'set':st,'err':r.stderr[-200:]}
    else:
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(c,orig)
        res={'set':st,'ratio':round(rr,5),'bytes':len(c),'slots':sd}
        if os.environ.get('KEEPBIN'): open(os.environ['KEEPBIN'],'wb').write(c)
    subprocess.run(['rm','-rf',d])
    print(json.dumps(res),flush=True)
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
