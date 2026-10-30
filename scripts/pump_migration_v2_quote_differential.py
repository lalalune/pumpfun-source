#!/usr/bin/env python3
"""Bounded migrate_v2 checks for post-completion quote funding."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pump_migrate_v2_probe as fixture
from pump_diagnostic_audit import audit
from pump_differential_output import PumpReport

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--candidate',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--allow-mismatches',action='store_true')
 args=parser.parse_args();candidate=args.candidate.resolve()
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 paths=[Path(__file__),Path(fixture.__file__),candidate,ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/upstream/pump.json',ROOT/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json']
 paths += [ROOT/'evidence'/x/'deployed.so'for x in ['original/pump_amm','dependencies/spl_token','dependencies/spl_token_2022','dependencies/associated_token']]
 record=candidate.parent/'build-comparison.json'
 if record.is_file():paths.append(record)
 publisher=PumpReport(args.output,ROOT,candidate,__file__,extra_inputs=paths)
 bound={str(p.resolve()):sha(p)for p in paths}
 saved=fixture.SAVED['curve'];data=base64.b64decode(saved['data_base64']);real=int.from_bytes(data[32:40],'little');limit=2**64-1
 cases=[]
 for boost in [False,True]:
  for funded in [False,True]:
   for post in [0,1,10**6,10**9]:
    cases.append({'name':f'post-{post}-boost-{boost}-funded-{funded}','boost':boost,'mutations':{'bonding_curve':{'patches':[(158,post.to_bytes(8,'little').hex())], 'lamports':saved['lamports']+(post if funded else 0)}}})
 for reserve,post in [(real,limit),(limit,1),(limit,limit),(0,limit)]:
  cases.append({'name':f'boundary-{reserve}-{post}','boost':True,'mutations':{'bonding_curve':{'patches':[(32,reserve.to_bytes(8,'little').hex()),(158,post.to_bytes(8,'little').hex())]}}})
 import copy
 for original_case in list(cases):
  c=copy.deepcopy(original_case);c['name']+='-stable';c['stable']=True
  c['mutations']['bonding_curve'].pop('lamports',None)
  if 'funded-True' in c['name']:
   post=int.from_bytes(bytes.fromhex(next(v for off,v in c['mutations']['bonding_curve']['patches']if off==158)),'little')
   c['mutations']['associated_quote_bonding_curve']={'patches':[(64,(85005359063+post).to_bytes(8,'little').hex())]}
  cases.append(c)
 rows=[]
 for c in cases:
  left,right=fixture.run(c),fixture.run(c,candidate)
  for value in [left,right]:value['events']=[line for line in value['logs']if line.startswith('Program data:')]
  different=[key for key in ['error','before','after','events','inner','return']if left[key]!=right[key]]
  rows.append({'case':c,'original':left,'candidate':right,'different_fields':different})
 diagnostics=audit({'post_completion_quote':{'cases':rows}})
 assert bound=={str(p.resolve()):sha(p)for p in paths},'Inputs changed during execution'
 report={'scope':__doc__+' Synthetic states and signed local transactions; controls can overlap. No live transactions or whole-binary claim.', 'candidate_sha256':sha(candidate),'original_sha256':sha(ROOT/'evidence/original/pump/deployed.so'),'bound_inputs_sha256':bound,'case_count':len(rows),'mismatches':[i for i,row in enumerate(rows)if row['different_fields']],'diagnostics':diagnostics,'cases':rows}
 raw=json.dumps(report,separators=(',',':')).encode();publisher.write(gzip.compress(raw,mtime=0)if args.output.name.endswith('.gz')else raw)
 print(json.dumps({'case_count':len(rows),'mismatches':report['mismatches'],'diagnostic_mismatches':len(diagnostics['mismatches'])}))
 return 0 if args.allow_mismatches else bool(report['mismatches']or diagnostics['mismatches'])
if __name__=='__main__':raise SystemExit(main())
