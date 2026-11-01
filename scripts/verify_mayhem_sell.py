#!/usr/bin/env python3
"""Offline verification of saved signed sell receipts; never executes a VM or RPC."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

from pathlib import Path
from pump_differential_output import PumpReport
from mayhem_receipt_comparison import same_json_value
import argparse, base64, gzip, hashlib, json, re, struct
from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT=Path(__file__).resolve().parents[1]
MAY=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
sha=lambda b:hashlib.sha256(b).hexdigest()
number=lambda d,o,n=8,signed=False:int.from_bytes(d[o:o+n],'little',signed=signed)
data=lambda a:base64.b64decode(a['data_base64'])
def shortvec(v):
 n=sum((b&127)<<(7*i) for i,b in enumerate(v[0]));raw=bytes(v[1:]);assert len(raw)==n;return raw
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--receipts',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();report_output=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=(a.receipts,ROOT/'evidence/original/mayhem/deployed.so'))
 raw=a.receipts.read_bytes();report=json.loads(gzip.decompress(raw) if a.receipts.suffix=='.gz' else raw);assert report['candidate_sha256']==sha(a.candidate.read_bytes())
 assert report['original_sha256']==sha((ROOT/'evidence/original/mayhem/deployed.so').read_bytes())
 if not report['harness_sha256']: raise ValueError('receipt binds no harness file')
 report_output.inputs.extend(ROOT/path for path in report['harness_sha256'])
 for path,digest in report['harness_sha256'].items():assert sha((ROOT/path).read_bytes())==digest
 if type(report.get('case_count')) is not int or report['case_count']<=0: raise ValueError('case_count must be a positive integer')
 assert report['case_count']==len(report['cases']) and not report['mismatches']
 successes=failures=quote_checks=event_checks=rollback_checks=0
 for pair in report['cases']:
  c=pair['case'];o=pair['original'];b=pair['candidate'];assert not pair['different_fields']
  # Bind the executable snapshots actually retained by each VM run, not
  # only the report header supplied alongside a selected candidate file.
  for side in ('original','candidate'):
   for phase in ('before','after'):
    program=pair[side][phase].get(str(MAY))
    if (not isinstance(program,dict) or program.get('executable') is not True
        or program.get('data_sha256')!=report[side+'_sha256']):
     raise ValueError(side+' '+phase+': Mayhem executable snapshot differs from declared image')
  assert o['transaction_base64']==b['transaction_base64'] and same_json_value(o['error'],b['error'])
  for phase in ['before','after']:
   assert same_json_value({k:v for k,v in o[phase].items() if k!=str(MAY)},{k:v for k,v in b[phase].items() if k!=str(MAY)})
  for field in ['inner_instructions','return_data']:assert same_json_value(o['metadata'][field],b['metadata'][field])
  for r in [o,b]:
   tx=Transaction.from_bytes(base64.b64decode(r['transaction_base64']));keys=tx.message.account_keys
   assert (tx.signatures and all(tx.verify_with_results())) and r['signature_verified']
   assert r['signature']==str(tx.signatures[0])==r['metadata']['signature']
   required=tx.message.header.num_required_signatures
   assert required in [1,2] and all(k.is_on_curve() for k in keys[:required])
   assert set(map(str,keys))<=r['before'].keys() and r['before'].keys()==r['after'].keys()
   for phase in ['before','after']:
    for account in r[phase].values():
     if account is not None and not account['executable']:assert sha(data(account))==account['data_sha256']
   payer=str(keys[0]);expected=dict(r['before'][payer],lamports=r['before'][payer]['lamports']-5000*required)
   assert same_json_value(r['after'][payer],expected)
   ix=tx.message.instructions[-1];assert keys[ix.program_id_index]==MAY
   if bytes(ix.data[:8])!=hashlib.sha256(b'global:sell').digest()[:8]: raise ValueError('expected Mayhem sell instruction')
   if r['error'] is not None:
    assert all(same_json_value(r['before'][key],r['after'][key]) for key in r['before'] if key!=payer)
    rollback_checks+=1;continue
   assert len(ix.accounts)>=21 and bytes(ix.data[:8])==hashlib.sha256(b'global:sell').digest()[:8]
   outer=[keys[i] for i in ix.accounts];gkey,skey,solkey,mintkey,vkey,curvekey=map(str,[outer[i] for i in [1,2,3,4,5,9]])
   assert required==2 and outer[0]==keys[1] and str(outer[0])==r['synthetic_trader']
   assert outer[1]==Pubkey.find_program_address([b'global-params'],MAY)[0]
   assert outer[2]==Pubkey.find_program_address([b'mayhem-state',bytes(outer[4])],MAY)[0]
   assert outer[3]==Pubkey.find_program_address([b'sol-vault'],MAY)[0]
   assert outer[19]==Pubkey.find_program_address([b'bonding-curve-v2',bytes(outer[4])],MAY)[0]
   before_g=data(r['before'][gkey]);before_s=data(r['before'][skey]);before_v=data(r['before'][vkey]);before_c=data(r['before'][curvekey]).ljust(141,b'\0')
   g=data(r['after'][gkey]);s=data(r['after'][skey]);v=data(r['after'][vkey]);curve=data(r['after'][curvekey]).ljust(141,b'\0')
   assert before_g[81:113]==bytes(outer[0])
   vt,vs,rt,rs=struct.unpack_from('<QQQQ',before_c,8);tokens=number(before_v,64);cap=number(before_g,16);retained=number(bytes(ix.data),26,2)
   output=vs*tokens//(vt+tokens)
   if cap:output=min(output,cap)
   output=min(output,rs*(10000-retained)//10000);input_tokens=output*vt//(vs-output)
   direct=[i['instruction'] for group in r['metadata']['inner_instructions'] for i in group if i['stackHeight']==2 and keys[i['instruction']['programIdIndex']]==PUMP]
   assert len(direct)==1 and shortvec(direct[0]['data'])==bytes.fromhex('33e685a4017f83ad')+struct.pack('<QQ',input_tokens,max(output-1,0))
   assert [keys[i] for i in shortvec(direct[0]['accounts'])]==[outer[i] for i in [8,10,4,9,11,5,3,7,12,6,13,14,15,16,19,20]]
   quote_checks+=1
   sol=r['after'][solkey]['lamports']-r['before'][solkey]['lamports'];sold=number(before_v,64)-number(v,64);now=c.get('now',100)
   expected_g=bytearray(before_g);expected_g[113:129]=(number(before_g,113,16,True)-sol).to_bytes(16,'little',signed=True)
   expected_s=bytearray(before_s);expected_s[56:72]=(number(before_s,56,16,True)-sol).to_bytes(16,'little',signed=True)
   expected_s[72:88]=(number(before_s,72,16,True)+sold).to_bytes(16,'little',signed=True);expected_s[89:97]=(now%(1<<64)).to_bytes(8,'little');expected_s[97]=1
   assert g==expected_g and s==expected_s
   vtp,vsp,rtp,rsp=struct.unpack_from('<QQQQ',curve,8)
   event=bytes.fromhex('31487b2d6e40b08501')+bytes(outer[3])+bytes(outer[4])
   event+=struct.pack('<QQQQ',sol,sold,r['after'][solkey]['lamports'],number(v,64))
   event+=s[56:88]+struct.pack('<QQ',vsp,vtp)+g[113:129]+struct.pack('<qqQQIH',now,number(s,16,8,True),rsp,rtp,number(g,162,4),retained)
   event+=struct.pack('<QQ',sol,r['after'][solkey]['lamports'])+s[56:72]+struct.pack('<Q',vsp)+g[113:129]+struct.pack('<Q',rsp)+bytes(32)
   assert len(event)==303 and ['Program data: '+base64.b64encode(event).decode()]==[line for line in r['metadata']['logs'] if line.startswith('Program data: ') and base64.b64decode(line[14:])[:8]==event[:8]]
   selfcalls=[i['instruction'] for group in r['metadata']['inner_instructions'] for i in group if i['stackHeight']==2 and keys[i['instruction']['programIdIndex']]==MAY]
   assert len(selfcalls)==1 and shortvec(selfcalls[0]['data'])==bytes.fromhex('e445a52e51cb9a1d')+event
   event_checks+=1
  successes+=o['error'] is None;failures+=o['error'] is not None
 result={'scope':__doc__,'receipt_sha256':sha(raw),'candidate_sha256':report['candidate_sha256'],'original_sha256':report['original_sha256'],'case_count':report['case_count'],'verified_signed_transactions':2*report['case_count'],'successful_cases':successes,'rejection_cases':failures,'successful_quote_and_cpi_checks':quote_checks,'complete_event_and_state_checks':event_checks,'complete_failed_transaction_rollback_checks':rollback_checks,'mismatches':[]}
 report_output.write((json.dumps(result,indent=2)+'\n').encode("utf-8"));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
