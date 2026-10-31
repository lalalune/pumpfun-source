#!/usr/bin/env python3
"""mirmap.py <dir> <map.json> [tag]: apply a full FI->colour map (from sscsim) to ssc.mir, llc -start-after=stack-slot-coloring, score"""
import sys,re,os,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T+'/../t139'); sys.path.insert(0,T); import px2, fixfs
D=sys.argv[1]; new={int(k):v for k,v in json.load(open(sys.argv[2])).items()}; tag=sys.argv[3] if len(sys.argv)>3 else 'map'
log=open(D+'/ssc.log').read()
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
pre=open(D+'/pre.mir').read().split('\n'); ssc=open(D+'/ssc.mir').read().split('\n')
bp=pre.index('body:             |'); bs=ssc.index('body:             |'); assert len(pre)-bp==len(ssc)-bs
out=list(ssc); n=0
for k in range(bp,len(pre)):
    l=pre[k]; fs=set(int(x) for x in re.findall(r'%stack\.(\d+)\b',l)); s=ssc[bs+(k-bp)]
    rep={}
    for f in fs:
        if f in COL and new.get(f,COL[f])!=COL[f]: rep[COL[f]]=new[f]
    if rep:
        s=re.sub(r'%stack\.(\d+)\b',lambda m:'%stack.'+str(rep.get(int(m.group(1)),int(m.group(1)))),s); n+=1
    out[bs+(k-bp)]=s
nm=D+'/'+tag; open(nm+'.mir','w').write('\n'.join(out))
r=subprocess.run([D+'/llc.sh',nm+'.mir','-start-after=stack-slot-coloring','-filetype=obj','-o',nm+'.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-800:]); sys.exit(1)
c=fixfs.fixfs(px2.G['elf_fn'](nm+'.o',px2.G['KEEP'])); open(nm+'.bin','wb').write(c); os.remove(nm+'.o'); os.remove(nm+'.mir')
s=px2.score_bin(c); print(json.dumps({'tag':tag,'lines':n,**{k:s[k] for k in('ratio','M','bytes')}}))
