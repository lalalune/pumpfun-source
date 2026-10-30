#!/usr/bin/env python3
"""Independent offline saved-receipt checks for both Mayhem PumpSwap trades; no VM or RPC."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

from pathlib import Path
import argparse,base64,gzip,hashlib,json,struct
from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'evidence/original/mayhem/deployed.so').is_file())
MAY=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e');AMM=Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
sha=lambda b:hashlib.sha256(b).hexdigest()
num=lambda d,o,n=8,signed=False:int.from_bytes(d[o:o+n],'little',signed=signed)
data=lambda a:b'' if a is None else base64.b64decode(a['data_base64'])
def vec(v):
 n=sum((b&127)<<(7*i) for i,b in enumerate(v[0]));b=bytes(v[1:]);assert len(b)==n;return b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--receipts',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 raw=a.receipts.read_bytes();report=json.loads(gzip.decompress(raw) if a.receipts.suffix=='.gz' else raw)
 assert report['candidate_sha256']==sha(a.candidate.read_bytes());assert report['original_sha256']==sha((ROOT/'evidence/original/mayhem/deployed.so').read_bytes())
 for path,digest in report['harness_sha256'].items():assert sha((ROOT/path).read_bytes())==digest
 if type(report.get('case_count')) is not int or report['case_count']<=0: raise ValueError('case_count must be a positive integer')
 assert report['case_count']==len(report['cases']) and not report['mismatches']
 successes=failures=quote_checks=events=rollbacks=0
 for pair in report['cases']:
  c=pair['case'];o=pair['original'];b=pair['candidate'];assert not pair['different_fields'];assert o['transaction_base64']==b['transaction_base64'] and o['error']==b['error']
  for phase in ['before','after']:assert {k:v for k,v in o[phase].items() if k!=str(MAY)}=={k:v for k,v in b[phase].items() if k!=str(MAY)}
  for field in ['inner_instructions','return_data']:assert o['metadata'][field]==b['metadata'][field]
  for r in [o,b]:
   tx=Transaction.from_bytes(base64.b64decode(r['transaction_base64']));keys=tx.message.account_keys;assert all(tx.verify_with_results()) and r['signature_verified'];assert r['signature']==str(tx.signatures[0])==r['metadata']['signature']
   required=tx.message.header.num_required_signatures;assert required in [1,2] and all(k.is_on_curve() for k in keys[:required]);assert set(map(str,keys))<=r['before'].keys() and r['before'].keys()==r['after'].keys()
   for phase in ['before','after']:
    for ac in r[phase].values():
     if ac is not None and not ac['executable']:assert sha(data(ac))==ac['data_sha256']
   payer=str(keys[0]);assert r['after'][payer]==dict(r['before'][payer],lamports=r['before'][payer]['lamports']-5000*required)
   ix=tx.message.instructions[-1];assert keys[ix.program_id_index]==MAY
   if c.get('instruction') not in ('buy_pump_swap','sell_pump_swap'): raise ValueError('expected Mayhem PumpSwap trade label')
   if bytes(ix.data[:8])!=hashlib.sha256(('global:'+c['instruction']).encode()).digest()[:8]: raise ValueError('Mayhem PumpSwap instruction does not match the declared trade')
   if r['error'] is not None:
    assert all(r['before'][key]==r['after'][key] for key in r['before'] if key!=payer);rollbacks+=1;continue
   buy=c['instruction']=='buy_pump_swap';assert c['instruction'] in ['buy_pump_swap','sell_pump_swap'];assert bytes(ix.data[:8])==hashlib.sha256(('global:'+c['instruction']).encode()).digest()[:8];assert len(ix.accounts)>=(31 if buy else 29)
   outer=[keys[i] for i in ix.accounts];assert required==2 and outer[0]==keys[1] and str(outer[0])==r['synthetic_trader']
   assert outer[1]==Pubkey.find_program_address([b'global-params'],MAY)[0];assert outer[2]==Pubkey.find_program_address([b'mayhem-state',bytes(outer[3])],MAY)[0];assert outer[6]==Pubkey.find_program_address([b'sol-vault'],MAY)[0]
   assert outer[28 if buy else 26]==Pubkey.find_program_address([b'pool-v2',bytes(outer[3])],MAY)[0]
   native=str(outer[13])=='So11111111111111111111111111111111111111112';gk,sk,solk,vk,qk,pk,pbk,pqk=map(str,[outer[i] for i in [1,2,6,4,5,11,14,15]])
   bg,bs,bv=data(r['before'][gk]),data(r['before'][sk]),data(r['before'][vk]);g,s,v=data(r['after'][gk]),data(r['after'][sk]),data(r['after'][vk]);pool=data(r['before'][pk]).ljust(287,b'\0')
   assert bg[81:113]==bytes(outer[0]);vt=num(data(r['before'][pbk]),64);vs=num(data(r['before'][pqk]),64)+num(pool,245,16,True);tokens=num(bv,64);cap=num(bg,16 if native else 182);retained=num(bytes(ix.data),26,2);output=vs*tokens//(vt+tokens)
   if cap:output=min(output,cap)
   output=min(output,vs*(10000-retained)//10000);input_tokens=output*vt//(vs+output if buy else vs-output);limit=output if buy else max(0,output-1)
   direct=[i['instruction'] for group in r['metadata']['inner_instructions'] for i in group if i['stackHeight']==2 and keys[i['instruction']['programIdIndex']]==AMM]
   assert len(direct)==1 and vec(direct[0]['data'])==bytes.fromhex('66063d1201daebea' if buy else '33e685a4017f83ad')+struct.pack('<QQ',input_tokens,limit)+(b'\0' if buy else b'')
   order=[11,6,12,3,13,4,5,14,15,16,17,9,8,7,10,18,19,20,21]+([22,23,24,25,29,30] if buy else [22,23,27,28]);assert [keys[i] for i in vec(direct[0]['accounts'])]==[outer[i] for i in order];quote_checks+=1
   before_quote=r['before'][solk]['lamports'] if native else num(data(r['before'][qk]),64);after_quote=r['after'][solk]['lamports'] if native else num(data(r['after'][qk]),64)
   quote=(before_quote-after_quote) if buy else (after_quote-before_quote);traded=(num(v,64)-num(bv,64)) if buy else (num(bv,64)-num(v,64));now=c.get('now',100);goff=113 if native else 206;sign=1 if buy else -1
   eg=bytearray(bg);eg[goff:goff+16]=(num(bg,goff,16,True)+sign*quote).to_bytes(16,'little',signed=True);es=bytearray(bs);es[56:72]=(num(bs,56,16,True)+sign*quote).to_bytes(16,'little',signed=True);es[72:88]=(num(bs,72,16,True)-sign*traded).to_bytes(16,'little',signed=True);es[89:97]=(now%(1<<64)).to_bytes(8,'little');es[97]=1;assert g==eg and s==es
   if buy:
    if num(g,goff,16,True)>0:assert (num(g,goff,16,True)&((1<<64)-1))<num(g,32 if native else 190)
    if num(s,56,16,True)>0:assert (num(s,56,16,True)&((1<<64)-1))<num(g,40 if native else 198)
   vtp=num(data(r['after'][pbk]),64);vsp=num(data(r['after'][pqk]),64)
   event=bytes.fromhex('31487b2d6e40b085')+bytes([0 if buy else 1])+bytes(outer[6])+bytes(outer[3]);event+=struct.pack('<QQQQ',quote if native else 0,traded,after_quote if native else 0,num(v,64));event+=(s[56:72] if native else bytes(16))+s[72:88]+struct.pack('<QQ',vsp if native else 0,vtp)+(g[113:129] if native else bytes(16))+struct.pack('<qqQQIH',now,num(s,16,8,True),vsp if native else 0,vtp,num(g,162,4),retained);event+=struct.pack('<QQ',quote,after_quote)+s[56:72]+struct.pack('<Q',vsp)+g[goff:goff+16]+struct.pack('<Q',vsp)+(bytes(32) if native else bytes(outer[13]))
   assert len(event)==303 and ['Program data: '+base64.b64encode(event).decode()]==[line for line in r['metadata']['logs'] if line.startswith('Program data: ') and base64.b64decode(line[14:])[:8]==event[:8]]
   selfcalls=[i['instruction'] for group in r['metadata']['inner_instructions'] for i in group if i['stackHeight']==2 and keys[i['instruction']['programIdIndex']]==MAY];assert len(selfcalls)==1 and vec(selfcalls[0]['data'])==bytes.fromhex('e445a52e51cb9a1d')+event;events+=1
  successes+=o['error'] is None;failures+=o['error'] is not None
 result={'scope':__doc__,'receipt_sha256':sha(raw),'candidate_sha256':report['candidate_sha256'],'original_sha256':report['original_sha256'],'case_count':report['case_count'],'verified_signed_transactions':2*report['case_count'],'successful_cases':successes,'rejection_cases':failures,'successful_quote_and_cpi_checks':quote_checks,'complete_event_and_state_checks':events,'complete_failed_transaction_rollback_checks':rollbacks,'mismatches':[]};a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
