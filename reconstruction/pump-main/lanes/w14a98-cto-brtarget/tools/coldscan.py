#!/usr/bin/env python3
"""coldscan.py <mn.ll> <out.jsonl> <groups idx csv> : move cold error groups (to_string+alloc-fail, or exit) in post-opt IR to every
position after a block in the validate span, real llc. RA-neutral by construction (cold blocks), check fM/skM."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T); import irord
G=[['bb10.i','bb3.i30.i'],['bb17.i','bb3.i23.i'],['bb79.i','bb3.i58.i'],['bb27.i','bb3.i37.i'],['bb39.i','bb3.i51.i'],['bb32.i','bb3.i44.i'],['bb48.i','bb3.i292'],
   ['exit31.i'],['exit24.i'],['exit59.i'],['exit38.i'],['exit52.i'],['exit45.i'],['exit293']]
ll,out=sys.argv[1],sys.argv[2]; gi=[int(x) for x in sys.argv[3].split(',')]; base=os.environ.get('BASE','')
t=open(ll).read(); pre,bl,post=irord.split(t); nm=[irord.short(b[0]) for b in bl]
lo=nm.index('bb6.i'); hi=nm.index('bb65.i')
anchors=nm[lo:hi+1]
done=set()
if os.path.exists(out):
    for l in open(out): done.add(json.loads(l)['spec'])
for g in gi:
    for a in anchors:
        if a in G[g]: continue
        mv=[f'{G[g][0]}@{a}']+[f'{G[g][k]}@{G[g][k-1]}' for k in range(1,len(G[g]))]
        spec='mv:'+';'.join(([base] if base else [])+mv)
        if spec in done: continue
        r=irord.run(ll,O+f'/tmp/cs{g}',spec)
        with open(out,'a') as f: f.write(json.dumps({'spec':spec,'g':g,'after':a,**{k:r.get(k) for k in ('M','bytes','jM','fM','skM','err')}})+'\n')
