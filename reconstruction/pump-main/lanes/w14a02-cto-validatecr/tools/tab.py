import sys,json,os
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R={}
for l in open(O+'/results.jsonl'):
    try: d=json.loads(l); R[d['name']]=d
    except: pass
for l in open(sys.argv[1] if len(sys.argv)>1 else O+'/chunks.jsonl'):
    d=json.loads(l); r=R.get(d['name'],{})
    print('%-14s %5d %-8s fm %.5f rm %.5f rmV %3d rmT %4d | L rm %3d fm %3d n %s | %s'%(d['name'],d['bytes'],r.get('ratio'),d['fm'],d['rm'],d['rmV'],d['rmT'],d['Lrm'],d['Lfm'],d['Ln'],' '.join('%2d'%x for x in d['rmC'])))
