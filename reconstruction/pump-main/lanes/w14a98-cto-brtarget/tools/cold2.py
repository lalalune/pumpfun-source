import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T); import irord
rs=[json.loads(l) for l in open(O+'/coldscan_963d1ee.jsonl')]; rs=[r for r in rs if r.get('M')]
firsts=sorted(rs,key=lambda r:-r['jM'])[:12]
seconds=sorted(rs,key=lambda r:-(r['M']*2+r['jM']))[:45]
k=int(sys.argv[1]); n=int(sys.argv[2]); out=sys.argv[3]
for i,a in enumerate(firsts):
    if i%n!=k: continue
    for b in seconds:
        if a['g']==b['g']: continue
        spec=a['spec']+';'+b['spec'][3:]
        r=irord.run(O+'/tmp/mn.ll',O+f'/tmp/c2_{k}',spec)
        open(out,'a').write(json.dumps({'spec':spec,**{x:r.get(x) for x in ('M','bytes','jM','fM','err')}})+'\n')
