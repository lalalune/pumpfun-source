#!/usr/bin/env python3
"""Unmodified original/candidate SBF comparison with ordinary signatures and synthetic accounts."""
from pathlib import Path
import json,hashlib,base64,argparse,re
import mayhem_sell_v2_fixture as p
from pump_amm_reusable_harness import pin_program
from solders.transaction import Transaction
D=Path(__file__).resolve().parent
def cases(path):
 return json.loads(path.read_text())['cases']

def normlogs(logs):
 out=[]
 for l in logs:
  if re.search(r' consumed \d+ of \d+ compute units',l):continue
  l=re.sub(r'AnchorError thrown in .+?:\d+\.', 'AnchorError thrown in <source>.',l)
  if 'panicked at' in l:continue
  out.append(l)
 return out

def limit_value(text):
 value=int(text)
 if value<0:raise argparse.ArgumentTypeError('--limit must not be negative')
 return value

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--limit',type=limit_value);ap.add_argument('--cases',type=Path,required=True);ap.add_argument('--family',choices=['native','token','token22'],required=True);a=ap.parse_args();a.candidate=pin_program(a.candidate);rows=[];mismatches=[]
 for c in cases(a.cases)[:a.limit]:
  c=dict(c,token_quote=a.family!='native',quote_token22=a.family=='token22')
  original=p.run(c);candidate=p.run(c,a.candidate);diff=[]
  for r in [original,candidate]:
   tx=Transaction.from_bytes(base64.b64decode(r['transaction_base64']));assert all(tx.verify_with_results())
  if original['transaction_base64']!=candidate['transaction_base64']:diff.append('signed_transaction')
  for phase in ['before','after']:
   x={k:v for k,v in original[phase].items() if k!=str(p.MAY)};y={k:v for k,v in candidate[phase].items() if k!=str(p.MAY)}
   if x!=y:diff.append(phase)
  if original['error']!=candidate['error']:diff.append('error')
  for field in ['inner_instructions','return_data']:
   if original['metadata'][field]!=candidate['metadata'][field]:diff.append(field)
  ev=lambda r:[l for l in r['metadata']['logs'] if l.startswith('Program data: ')]
  if ev(original)!=ev(candidate):diff.append('events')
  logdiff=normlogs(original['metadata']['logs'])!=normlogs(candidate['metadata']['logs'])
  row={'case':c,'original':original,'candidate':candidate,'different_fields':diff,'normalized_log_difference':logdiff};rows.append(row)
  if diff:mismatches.append({'case':c['name'],'fields':diff,'original_error':original['error'],'candidate_error':candidate['error']})
  print(c['name'],original['error'],diff,flush=True)
 report={'scope':__doc__,'candidate_sha256':p.sha(a.candidate.read_bytes()),'candidate_bytes':a.candidate.stat().st_size,'original_sha256':p.sha((p.ROOT/'evidence/original/mayhem/deployed.so').read_bytes()),'case_count':len(rows),'successful_original_cases':sum(r['original']['error'] is None for r in rows),'signed_transactions':2*len(rows),'mismatches':mismatches,'normalized_log_differences':[r['case']['name'] for r in rows if r['normalized_log_difference']],'harness_sha256':{str(x.relative_to(p.ROOT)):p.sha(x.read_bytes()) for x in [Path(__file__).resolve(),D/'mayhem_sell_v2_fixture.py',p.ROOT/'scripts/pump_trade_fixture.py',a.cases.resolve(),p.ROOT/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json']},'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['case_count','successful_original_cases','mismatches']}));raise SystemExit(bool(mismatches))
if __name__=='__main__':main()
