#!/usr/bin/env python3
"""Extend frozen legacy sell fixtures with stored creator-fee overrides; no live RPC."""
import argparse,hashlib,json,struct
from pathlib import Path
import pump_legacy_sell_differential as f
from pump_differential_output import PumpReport
from pump_trade_fixture import REPORT_INPUTS

def cases():
 out=[]
 for bps in [0,1,30,500,10000,10001,2**64-1]:
  for mode in ['normal','cashback','holder','creator_zero']:
   c={'name':f'configured_fee_{bps}_{mode}','curve_bytes':[(115+i,v) for i,v in enumerate(struct.pack('<Q',bps))]}
   if mode=='cashback':c['curve_bytes'].append([82,1]);c['cashback_account']=True
   if mode=='holder':c['curve_bytes'].append([124,1])
   if mode=='creator_zero':c['curve_bytes'] += [[i,0] for i in range(49,81)]
   out.append(c)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--include-baseline',action='store_true');a=ap.parse_args();publisher=PumpReport(a.output,f.R,a.candidate,__file__,extra_inputs=REPORT_INPUTS);rows=[]
 for c in (f.cases() if a.include_baseline else [])+cases():
  o=f.run(c);b=f.run(c,a.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]];rows.append({'case':c,'original':o,'candidate':b,'match':not diff,'different_fields':diff})
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();d={'scope':'Normally signed synthetic legacy sell override regression; underlying legacy harness preserved. No full binary identity claim.','candidate_sha256':sha(f.pin_program(a.candidate)),'original_sha256':sha(f.R/'evidence/original/pump/deployed.so'),'harness_sha256':sha(Path(__file__)),'base_harness_sha256':sha(Path(f.__file__)),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if not r['match']],'cases':rows};publisher.write((json.dumps(d,indent=2)+'\n').encode('utf-8'));print(json.dumps({k:d[k] for k in ['case_count','mismatches','candidate_sha256']}));
 if d['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
