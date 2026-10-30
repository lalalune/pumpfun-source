import json,sys
for l in open(sys.argv[1]):
    if l.startswith('==='): print(l.strip()); continue
    n,rest=l.split(' ',1); j,_,fb=rest.partition('} ')
    d=json.loads(j+'}'); print(n, d['ratio'], d['slots'], d['bytes'], 'nloss',len(d['losses'] or []), 'rloss',len(d['rl'] or []), fb.strip(), d['err'][-100:] if not d['ok'] else '')
