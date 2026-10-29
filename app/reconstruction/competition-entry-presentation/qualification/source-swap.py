from pathlib import Path
import json,hashlib,sys,os
here=Path(__file__).resolve().parent;target=Path('/workspace/pump-app-leaderboard-navigation/app/packages/frontend/src/app/leaderboard/leaderboard-client.tsx');mode=sys.argv[1]
assert mode in ['baseline','candidate']
pins=json.loads((here/'SOURCE-SWAP.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(target.read_bytes()) in pins.values(),'Unknown local source edits'
b=(here/(mode+'-client.tsx')).read_bytes();assert sha(b)==pins[mode]
tmp=target.with_suffix('.prize-stage');tmp.write_bytes(b);os.replace(tmp,target)
print(json.dumps({'mode':mode,'sha256':sha(b)}))
