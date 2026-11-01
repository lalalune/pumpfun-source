#!/bin/bash
# mpq.sh name...: mp.py (M/Mperm/Mhc/LCS) + fuev (L---/Lrfj/swap) for IR-edited cells -> res-ir.jsonl rows like scr.py's
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for n in "$@"; do
  python3 - $n <<'PY'
import json,subprocess,sys
n=sys.argv[1]; r=json.load(open(f'rx/{n}/res.json')); r['genes']={'e1':'IR e1=hphi+hcs+hev (w14a142) on m0','hc':'IR hc=hphi+hcs on m0','e1T':'IR e1 on T','hcT':'IR hc on T'}.get(n,'IR')
q=subprocess.run(['python3','tools/mp.py','mp_'+n,f'rx/{n}/m.ll'],capture_output=True,text=True); j=json.loads(q.stdout.strip().splitlines()[-1])
r.update({k:j[k] for k in ('Mperm','Mhc','lcs','lcs_hc','lcs_f') if k in j})
q=subprocess.run(['python3','tools/fuev.py',f'rx/{n}/fn.bin'],capture_output=True,text=True); f=json.loads(q.stdout.strip().splitlines()[-1])
r.update({k:f[k] for k in ('L---','Lrfj','lcs_op','head_rfj','swap')})
open('res-ir.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps(r))
PY
done
