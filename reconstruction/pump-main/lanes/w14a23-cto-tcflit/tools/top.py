import json,sys
R=[]
for f in sys.argv[1:]:
    for l in open(f):
        try: R.append(json.loads(l))
        except: pass
ok=[r for r in R if 'ratio' in r]; bad=[r['name'] for r in R if 'ratio' not in r]
ok.sort(key=lambda r:-r['ratio'])
print(len(R),'results;',len(bad),'errors:',' '.join(bad))
for r in ok[:25]: print('%-24s %.5f %5d %s %s'%(r['name'],r['ratio'],r['bytes'],r['slots_diff'],'EQ' if r['eq_main'] else ''))
