#!/usr/bin/env python3
"""bwfm.py: like bwx.py (run/sweep) but scores plain ratio + frame-masked + skeleton (absratio) + C-chunk check.
  bwfm.py run <m.ll> SPEC [--keep DIR]
  bwfm.py sweep <m.ll> BASESPEC OUT.jsonl [-j N] [-w 1:2000,2000:1,inv] [--only lab1,lab2]"""
import sys,os,json,subprocess,tempfile,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bwx, absratio, struct
ORIGSEQ='289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556'
def errseq(raw):
    i=0; imms=[]; out=[]
    while i<len(raw):
        op,regs,off,imm=struct.unpack_from('<BBhi',raw,i)
        if op in (0x62,0x6a,0x72,0x7a): imms.append(imm)
        if op==0x85:
            lines=[x for x in imms if 280<=x<800]; codes=[x for x in imms if 2000<=x<6200]
            if lines and codes: out.append(lines[-1])
            imms=[]
        i+=16 if op==0x18 else 8
    return ' '.join(map(str,out))
from concurrent.futures import ThreadPoolExecutor
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a31-cto-lv3relayout')
OA=[absratio.norm(x,False) for x in absratio.O]; OS=[absratio.norm(x,True) for x in absratio.O]
def dis(o):
    h=subprocess.run([SDK+'/llvm-objdump','-h',o],capture_output=True,text=True).stdout
    import re
    sec=re.search(r'\.text\.\S*admin_cto7execute\S*',h).group(0)
    d=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--section='+sec,o],capture_output=True,text=True).stdout
    return [re.sub(r'^\s*\d+:\s*','',l).strip() for l in d.split('\n') if re.match(r'^\s*\d+:\s',l)]
def score(o,ot):
    rr,sd,nb=bwx.metric(bwx.elf_fn(o),ot); C=dis(o)
    fm=difflib.SequenceMatcher(None,OA,[absratio.norm(x,False) for x in C],autojunk=False).ratio()
    sk=difflib.SequenceMatcher(None,OS,[absratio.norm(x,True) for x in C],autojunk=False).ratio()
    es=errseq(bwx.elf_fn(o))
    return {'ratio':rr,'slots':sd,'bytes':nb,'fm':round(fm,5),'sk':round(sk,5),'es':es,'es_orig':es==ORIGSEQ}
def run(mod,spec,ot,keep=None):
    with tempfile.TemporaryDirectory(dir=OUT) as d:
        open(d+'/m.ll','w').write(bwx.apply(mod,spec))
        r=subprocess.run([bwx.LLC,*bwx.F,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'spec':spec,'error':r.stderr[-300:]}
        res={'spec':spec,**score(d+'/m.o',ot)}
        if keep: os.makedirs(keep,exist_ok=True); os.replace(d+'/m.o',keep+'/m.o'); os.replace(d+'/m.ll',keep+'/m.ll')
        return res
if __name__=='__main__':
    a=sys.argv[1:]; cmd=a.pop(0); mod=open(a.pop(0)).read(); ot=bwx.orig_toks()
    if cmd=='run':
        keep=a[a.index('--keep')+1] if '--keep' in a else None
        print(json.dumps(run(mod,a[0] if a and not a[0].startswith('--') else '',ot,keep)))
    elif cmd=='sweep':
        base=a.pop(0); outp=a.pop(0); j=int(a[a.index('-j')+1]) if '-j' in a else 4
        ws=a[a.index('-w')+1].split(',') if '-w' in a else ['1:2000','2000:1']
        only=a[a.index('--only')+1].split(',') if '--only' in a else None
        items=[]
        for lab,*_ in bwx.brs(mod):
            if only and lab not in only: continue
            for w in ws: items.append(f'bw:{lab}:{w}' if w!='inv' else f'inv:{lab}')
        f=open(outp,'a')
        def go(it):
            r=run(mod,(base+',' if base else '')+it,ot); r['item']=it; f.write(json.dumps(r)+'\n'); f.flush(); return r
        with ThreadPoolExecutor(j) as ex: list(ex.map(go,items))
