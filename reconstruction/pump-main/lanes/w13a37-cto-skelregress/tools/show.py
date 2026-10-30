import json,sys
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress'
pat=sys.argv[1] if len(sys.argv)>1 else ''
for l in open(OUT+'/results.jsonl'):
    d=json.loads(l)
    if pat not in d['name']: continue
    c=d.get('cto') or {}
    sk=d.get('skel') or ''
    p=sk.split()
    print(f"{d['name']:24s} {str(c.get('ratio')):8s} {str(c.get('slots_diff')):5s} {str(c.get('cand_bytes')):6s} L{len(d.get('losses') or [])}/{len(d.get('raw_losses') or [])} sk={p[1] if len(p)>1 else '-'} c5={p[7] if len(p)>7 else '-'} c9={p[11] if len(p)>11 else '-'} {'' if d.get('ok') else 'ERR '+str(d.get('err',''))[-150:]}")
