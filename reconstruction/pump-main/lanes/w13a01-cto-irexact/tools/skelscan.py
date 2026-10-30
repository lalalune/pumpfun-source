#!/usr/bin/env python3
"""skelscan.py <mod.ll> <outdir> <basespec> <items> [-j N]: for each item, llc base+item and report plain ratio, bytes and
skeleton ratio (frame offsets, registers and jump offsets masked, calls/lddw masked): code-structure closeness."""
import sys,os,re,json,subprocess,difflib,threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import iredit,ctoracle
from pathlib import Path
T=os.path.dirname(os.path.abspath(__file__))
def norm(s):
    s=re.sub(r'\s+<[^>]*>','',s)
    if s.startswith('call'): s='call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s)
    m=re.match(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',s)
    if s.startswith('j') and m: s=m.group(1)+'J'
    return re.sub(r'\br[0-9]\b','R',s)
OS=[norm(l.split(None,1)[1].strip()) for l in open(os.environ.get('ORIG_DIS',T+'/../orig.dis'))]
def skel(mo):
    d=subprocess.run([T+'/dis.sh',mo],capture_output=True,text=True).stdout
    C=[norm(l.split(None,1)[1].strip()) for l in d.splitlines() if l.strip()]
    return round(difflib.SequenceMatcher(None,OS,C,autojunk=False).ratio(),5)
def one(mod,out,spec):
    m=iredit.run_spec(mod,out,spec,keep=True)
    if 'ratio' in m: m['skel']=skel(str(Path(out)/'m.o'))
    return m
if __name__=='__main__':
    iredit.ORIG=ctoracle.orig_tokens()
    mod=open(sys.argv[1]).read(); out=Path(sys.argv[2]); base=sys.argv[3]
    items=[l.strip() for l in open(sys.argv[4]) if l.strip()] if len(sys.argv)>4 and os.path.exists(sys.argv[4]) else ['']
    j=int(sys.argv[sys.argv.index('-j')+1]) if '-j' in sys.argv else 4
    def f(it):
        spec=','.join(x for x in (base,it) if x)
        try: return it,one(mod,out/('w%d'%threading.get_ident()),spec)
        except Exception as e: return it,{'error':repr(e)[:200]}
    with ThreadPoolExecutor(j) as ex:
        for it,m in ex.map(f,items): print(json.dumps({'item':it,**m}),flush=True)
