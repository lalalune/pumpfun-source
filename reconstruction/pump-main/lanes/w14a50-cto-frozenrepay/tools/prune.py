import json,os,sys
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay')
lst,pre,out=sys.argv[1:4]
ref={}
for f in ('k2.jsonl','k1.ok.jsonl'):
    for l in open(O+'/'+f):
        d=json.loads(l)
        if 'error' in d: continue
        n=d['name'].split('_',1)[1]
        if f=='k2.jsonl' or n not in ref: ref.setdefault(n,(f,d))
keep=[];skip=0
for l in open(O+'/'+lst):
    n=l.strip(); k=n[len(pre):]
    r=ref.get(k)
    if r:
        f,d=r
        if f=='k2.jsonl' and d.get('eq_main'): skip+=1; continue
        if f=='k1.ok.jsonl' and d['ratio']==0.65558 and d['bytes']==27392: skip+=1; continue
        if d['ratio']<0.645: skip+=1; continue
    keep.append(n)
open(O+'/'+out,'w').write('\n'.join(keep)+'\n'); print(len(keep),'kept',skip,'skipped')
