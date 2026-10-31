#!/usr/bin/env python3
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pump_differential_output import PumpReport
from pump_creator_collect_differential import *
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112');QUOTE=Pubkey.from_bytes(bytes([77])*32)
IX=next(x for x in J['instructions'] if x['name']=='collect_creator_fee_v2')
def run(c,binary=None):
 vm=LiteSVM().with_transaction_history(0).with_sigverify(True);vm.add_program_from_file(P,binary or ROOT/'evidence/original/pump/deployed.so');vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [PAY,U]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 creator=P if c.get('executable') else U.pubkey();vault=Pubkey.find_program_address([b'creator-vault',bytes(creator)],P)[0]
 vm.set_account(vault,Account(c.get('native',1000000),b'',Pubkey.default()))
 quote=Pubkey.from_string(c.get('quote',str(WSOL)));token=TOKEN22 if c.get('token22') else TOKEN
 md=bytearray(82);md[44]=9 if quote==WSOL else 6;md[45]=1;vm.set_account(quote,Account(10**9,bytes(md),token))
 source=Pubkey.find_program_address([bytes(vault),bytes(token),bytes(quote)],ATA)[0];dest=Pubkey.find_program_address([bytes(creator),bytes(token),bytes(quote)],ATA)[0]
 for key,owner,amount,side in [(source,vault,c.get('tokens',12345),'source'),(dest,creator,77,'destination')]:
  if c.get(side+'_missing'):vm.set_account(key,Account(0,b'',Pubkey.default()));continue
  td=bytearray(165);td[:32]=bytes(quote);td[32:64]=bytes(owner);td[64:72]=amount.to_bytes(8,'little');td[108]=1;reserve=vm.minimum_balance_for_rent_exemption(165)
  if quote==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
  vm.set_account(key,Account(reserve+(amount if quote==WSOL else 0),bytes(td),token))
 names={'creator':creator,'creator_token_account':dest,'creator_vault':vault,'creator_vault_token_account':source,'quote_mint':quote,'quote_token_program':token,'associated_token_program':ATA,'system_program':Pubkey.default(),'event_authority':E,'program':P}
 for name,patch in c.get('patch',{}).items():
  key=names[name];a=vm.get_account(key);d=bytearray(a.data)
  for off,h in patch.get('bytes',[]):d[off:off+len(bytes.fromhex(h))]=bytes.fromhex(h)
  vm.set_account(key,Account(patch.get('lamports',a.lamports),bytes(d[:patch.get('length',len(d))]),Pubkey.from_string(patch.get('owner',str(a.owner)))))
 if 'wrong' in c:names[c['wrong']]=Pubkey.from_bytes(bytes([79])*32)
 metas=[AccountMeta(names[a['name']],False,a.get('writable',False) and a['name']!=c.get('readonly')) for a in IX['accounts']];metas=metas[:c.get('account_count',len(metas))]
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(P,bytes(IX['discriminator']),metas)],PAY.pubkey(),[PAY],vm.latest_blockhash());assert all(tx.verify_with_results());keys=set(names.values())|{PAY.pubkey()}
 def snap():
  return {str(k):json.loads(vm.get_account(k).to_json()) if vm.get_account(k) and not vm.get_account(k).executable else None for k in keys}
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return dict(error=str(r.err()) if fail else None,before=before,after=snap(),events=[l for l in m.logs() if l.startswith('Program data: ')],inner=raw['inner_instructions'],returns=raw['return_data'],logs=m.logs(),transaction_base64=base64.b64encode(bytes(tx)).decode())
def cases():
 cases=[dict(quote=str(q),**c) for q in [WSOL,QUOTE] for c in [{},{'native':0},{'tokens':0},{'source_missing':True},{'destination_missing':True},{'token22':True},{'executable':True},{'native':890880},{'native':10**9},{'native':10**9,'destination_missing':True}]]
 for quote in [WSOL,QUOTE]:
  base={'quote':str(quote)}
  for target in ['creator_token_account','creator_vault','creator_vault_token_account','quote_mint']:
   for patch in [{'owner':str(P)},{'length':0},{'bytes':[(0,'ff')]},{'bytes':[(108,'02')]},{'bytes':[(108,'00')]}]:cases.append(dict(base,patch={target:patch}))
  cases += [dict(base,wrong=a['name']) for a in IX['accounts']]
  cases += [dict(base,readonly=a['name']) for a in IX['accounts'] if a.get('writable')]
  cases += [dict(base,tokens=0,destination_missing=True),dict(base,source_missing=True,native=0),dict(base,patch={'creator_token_account':{'bytes':[(32,bytes(32).hex())]}}),dict(base,patch={'creator_vault_token_account':{'bytes':[(32,bytes(32).hex())]}})]
  cases += [dict(base,account_count=n) for n in range(10)]
  for length in [0,64,71,72,100,164,165]:
   for amount in [0,12345]:cases.append(dict(base,tokens=amount,patch={'creator_vault_token_account':{'length':length}}))
  for flag in [0,2,255]:cases.append(dict(base,tokens=0,patch={'creator_vault_token_account':{'bytes':[(108,bytes([flag]).hex())]}}))
  cases += [dict(base,patch={'quote_mint':{'owner':str(TOKEN22)}}),dict(base,token22=True,patch={'quote_mint':{'owner':str(TOKEN)}})]
 return cases

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();output=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];paths=[Path(__file__),a.candidate,ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/upstream/pump.json']+[ROOT/f'evidence/dependencies/{n}/deployed.so' for n in ['spl_token','spl_token_2022','associated_token']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provenance={str(p):sha(p) for p in paths}
 for c in cases():
  o=run(c);n=run(c,a.candidate);diff=[k for k in ['error','before','after','events','inner','returns'] if o[k]!=n[k]];rows.append(dict(case=c,original=o,candidate=n,different_fields=diff))
 assert provenance=={str(p):sha(p) for p in paths}
 report={'original_sha256':provenance[str(ROOT/'evidence/original/pump/deployed.so')],'candidate_sha256':provenance[str(a.candidate)],'provenance':provenance,'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['different_fields']],'cases':rows};output.write((json.dumps(report,indent=2)+'\n').encode("utf-8"));print(json.dumps({k:report[k] for k in ['case_count','mismatches']}))
 if report['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
