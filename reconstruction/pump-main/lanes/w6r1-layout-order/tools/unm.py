import sys,json,subprocess
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-layout-order/reconstruction/harness'
P=[("0x1e7c0","9create_v27execute17"),("0x22a10","9admin_cto7execute17"),("0x5b3b0","8swap_hop17"),("0x72810","5sweep7execute17"),("0x80df8","12v3_buy_costs17"),("0x13b9b8","6buy_v211buy_handler17"),("0x13f630","26buy_exact_quote_in_handler17"),("0x1489f8","5trade15buy_exact_quote17")]
so=sys.argv[1]; ctl={}
if len(sys.argv)>2:
    for l in open(sys.argv[2]): w,b,_,ob,r,*_=l.split()+['']; ctl[w]=(b,r)
for w,s in P:
    o=subprocess.run(['python3',H+'/target_metric.py',so,w,'--sym',s],capture_output=True,text=True).stdout
    d=json.loads([l for l in o.splitlines() if l.startswith('{')][0])
    c=ctl.get(w); flag='' if not c or (c[0]==str(d['cand_bytes']) and c[1]==str(d['ratio'])) else f'  <-- was {c[0]} {c[1]}'
    print(w,d['cand_bytes'],'/',d['window_bytes'],d['ratio'],d.get('slots_diff',''),flag)
