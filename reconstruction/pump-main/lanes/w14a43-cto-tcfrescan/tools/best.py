import json,glob,sys
base=float(sys.argv[2]) if len(sys.argv)>2 else 0.65488
for f in sorted(glob.glob(sys.argv[1])):
    R=[]
    for l in open(f):
        try: R.append(json.loads(l))
        except: pass
    ok=[r for r in R if 'ratio' in r and r['bytes']==27400]; ok.sort(key=lambda r:-r['ratio'])
    allb=sorted([r for r in R if 'ratio' in r],key=lambda r:-r['ratio'])
    above=[r for r in ok if r['ratio']>base+1e-6]
    print('%-28s n=%4d best27400 %s %.5f | above=%d | bestany %s %.5f %d'%(f.split('/')[-1],len(R),ok[0]['lab'] if ok else '-',ok[0]['ratio'] if ok else 0,len(above),allb[0]['lab'],allb[0]['ratio'],allb[0]['bytes']))
    for r in above[:5]: print('    ',r)
