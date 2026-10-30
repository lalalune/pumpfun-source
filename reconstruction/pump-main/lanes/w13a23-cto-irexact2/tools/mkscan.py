#!/usr/bin/env python3
"""mkscan.py <post.ll> <prefix> [stride] [base]: write <prefix>_k.txt (8 files): mv every alloca before every stride-th alloca (+END), nolt, bw both ways, inv."""
import sys,re,subprocess,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import iredit
src,pre=sys.argv[1:3]; stride=int(sys.argv[3]) if len(sys.argv)>3 else 4
mod=open(src).read(); _,fn,_=iredit.split_fn(mod)
al=re.findall(r'^\s*%(\S+) = alloca',fn,re.M)
lt=set(re.findall(r'lifetime\.start\.p0\(i64 \d+, ptr (?:nonnull )?%(\S+)\)',fn))
brs=subprocess.run(['python3',os.path.dirname(os.path.abspath(__file__))+'/iredit.py','brs',src],capture_output=True,text=True).stdout.split()
anchors=al[::stride]+['END']; items=[]
for x in al:
    for a in anchors:
        if a!=x: items.append(f'mv:{x}:{a}')
items+=[f'nolt:{x}' for x in al if x in lt]
for b in brs: items+=[f'bw:{b}:2000:1',f'bw:{b}:1:2000',f'inv:{b}']
items=['{%s}'%i if ',' in i else i for i in items]
for k in range(8): open(f'{pre}_{k}.txt','w').write('\n'.join(items[k::8]))
print(len(items))
