#!/usr/bin/env python3
"""irB.py <name> [spec_file] [subset]: IR-order realisation of B on rx/<name>: resolve the spec on rx/<name>/mi.s by content
(from main), take each asm block's IR name, reorder the post-opt IR (instnamer'd mi.ll) and run real llc. Prints sc score."""
import sys,os,re,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sub, irord, relayn, sc, eseq
R=relayn.R
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
def prep(n):
    d=f'{O}/rx/{n}'
    if not os.path.exists(d+'/mi.ll'):
        subprocess.run([OPT,'-passes=instnamer',d+'/m.ll','-S','-o',d+'/mi.ll'],check=True)
    if not os.path.exists(d+'/mi.s'):
        subprocess.run(['bash',T+'/llc.sh',d+'/mi.ll',d+'/mi.s'],check=True)
    return d
def irnames(path):
    pre,bl,post=R.parse(path); m={}
    for n,b in bl:
        g=re.search(r'#\s*(%\S+)',b[0]) if n.startswith('LBB0') else re.search(r':\s*#\s*(%\S+)',b[0])
        if g: m[n]=g.group(1).strip('%')
    return m
def spec_ir(n,specn):
    d=prep(n); rs=sub.resolve_content(f'{O}/rx/main/mi.s',d+'/mi.s',specn); m=irnames(d+'/mi.s')
    out=[]
    for x,a in zip(specn,rs):
        if a is None or a not in m: continue
        s=irord.short(m[a]); 
        if s not in out: out.append(s)
    return out
if __name__=='__main__':
    n=sys.argv[1]; sf=sys.argv[2] if len(sys.argv)>2 else 'Bspec_O.txt'
    specn=open(f'{O}/tmp/{sf}').read().strip().split(',')
    if len(sys.argv)>3: specn=[x for x in specn if x in sys.argv[3].split(',')]
    prep('main'); sp=spec_ir(n,specn)
    d=f'{O}/rx/{n}'; os.makedirs(O+'/t',exist_ok=True)
    tag=os.environ.get('TAG','irB')
    r=irord.run(d+'/mi.ll',f'{O}/t/{n}_{tag}',','.join(sp)); r.pop('ch',None)
    r['eseq']=' '.join(map(str,eseq.seq(sc.fn(f'{O}/t/{n}_{tag}.s'))[:10])); r['spec']=','.join(sp)
    print(json.dumps(r))
