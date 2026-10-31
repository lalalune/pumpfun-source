#!/usr/bin/env python3
"""Normally signed local Pump admin_cto invoking PumpSwap through real CPI."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_donation_create_differential import *
import pump_validate_admin as pump
import pump_amm_admin_differential as amm
from pump_amm_reusable_harness import AMM_REPORT_INPUTS, pin_program
from pump_differential_output import PumpReport
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
IX=next(x for x in pump.IDL['instructions'] if x['name']=='admin_cto')
def ata(owner):return Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
def run_cto(c,binary=None):
 vm=LiteSVM().with_transaction_history(0);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('pump',PUMP),('pump_amm',AMM),('pump_fees',PROGRAM)]:vm.add_program_from_file(key,pin_program(binary if name=='pump_amm' and binary else ROOT/f'evidence/original/{name}/deployed.so'))
 for name,key in [('spl_token',TOKEN),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 gd=bytearray(pump.DATA);gd[418:450]=bytes(OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey());
 for off,val in c.get('pump_config_patches',[]):gd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 vm.set_account(pump.GLOBAL,Account(10**9,bytes(gd),PUMP));ad=bytearray(amm.RAW)
 for off,val in c.get('config_patches',[]):ad[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 vm.set_account(amm.CONFIG_KEY,Account(10**9,bytes(ad),AMM))
 for mint in [MINT,QUOTE]:
  md=bytearray(82);md[44]=9 if mint==QUOTE else 6;md[45]=1;vm.set_account(mint,Account(10**9,bytes(md),TOKEN))
 sd=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([Pubkey.find_program_address([b'sharing-config',bytes(MINT)],PROGRAM)[1],c.get('version',2),c.get('status',1)])+bytes(MINT)+bytes(AUTH.pubkey())+bytes([c.get('revoked',0)])+(1).to_bytes(4,'little')+bytes(AUTH.pubkey())+(10000).to_bytes(2,'little')
 if 'shareholders' in c:
  sd=sd[:76]+len(c['shareholders']).to_bytes(4,'little')+b''.join(bytes(Pubkey.from_string(key))+bps.to_bytes(2,'little') for key,bps in c['shareholders'])
 sd=bytearray(sd.ljust(1024,b'\0'))
 for off,val in c.get('sharing_patches',[]):sd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 sd=sd[:c.get('sharing_length',len(sd))]
 vm.set_account(SHARING,Account(10**9,bytes(sd),Pubkey.from_string(c.get('sharing_owner',str(PROGRAM)))))
 current=SHARING
 cd=bytearray(CURVE_DATA);cd[49:81]=bytes(current);cd[24:32]=(1000).to_bytes(8,'little');cd[48]=c.get('complete',1)
 for off,val in c.get('curve_patches',[]):cd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 vm.set_account(CURVE,Account(10**9,bytes(cd),PUMP))
 pd=hashlib.sha256(b'account:Pool').digest()[:8]+bytes([POOL_BUMP])+bytes(2)+bytes(POOL_AUTH)+bytes(MINT)+bytes(QUOTE)+bytes(96)+bytes(8)+bytes(SHARING)+bytes(2)+bytes(16)
 pd=bytearray(pd.ljust(301,b'\0'))
 for off,val in c.get('pool_patches',[]):pd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 pd=pd[:c.get('pool_length',len(pd))]
 vm.set_account(POOL,Account(c.get('pool_lamports',10**9),bytes(pd),Pubkey.from_string(c.get('pool_owner',str(AMM)))))
 vault=Pubkey.find_program_address([b'creator-vault',bytes(current)],PUMP)[0];holder=Pubkey.find_program_address([b'holder-rewards',bytes(MINT)],PUMP)[0];holdervault=Pubkey.find_program_address([b'creator-vault',bytes(holder)],PUMP)[0];ammvault=Pubkey.find_program_address([b'creator_vault',bytes(current)],AMM)[0]
 for key in [vault,holdervault,ammvault,ata(current),ata(vault),ata(holdervault),ata(ammvault),POOL_AUTH,pump.EVENT,amm.EVENT,EVENT]:vm.set_account(key,Account(0,b'',Pubkey.default()))
 names={'admin_set_creator_authority':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'quote_mint':QUOTE,'quote_token_program':TOKEN,'associated_token_program':ATA,'system_program':Pubkey.default(),'bonding_curve':CURVE,'current_creator':current,'current_creator_quote_token_account':ata(current),'creator_vault':vault,'creator_vault_quote_token_account':ata(vault),'holder_creator_vault':holdervault,'holder_creator_vault_quote_token_account':ata(holdervault),'pump_amm':AMM,'amm_global_config':amm.CONFIG_KEY,'pool_authority':POOL_AUTH,'pool':POOL,'pump_amm_event_authority':amm.EVENT,'coin_creator_vault_authority':ammvault,'coin_creator_vault_ata':ata(ammvault),'sharing_config':SHARING,'pump_fees':PROGRAM,'pump_fees_event_authority':EVENT,'event_authority':pump.EVENT,'program':PUMP}
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False),a.get('writable',False)) for a in IX['accounts']]
 assert not any(m.is_signer and m.pubkey==POOL_AUTH for m in metas)
 holderarg=b'\0' if 'holder' not in c else bytes([1,int(c['holder'])]);fee=b'\0' if 'fee_bps' not in c else b'\1'+c['fee_bps'].to_bytes(8,'little');new=b'\0' if c.get('new_none') else bytes([1])+bytes(Pubkey.from_string(c.get('new_creator',str(OTHER.pubkey()))))
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,bytes(IX['discriminator'])+holderarg+fee+new,metas)],PAYER.pubkey(),[PAYER,AUTH],vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for name,key in {**names,'transaction_payer':PAYER.pubkey()}.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   out[name]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;raw=json.loads(meta.to_json())
 return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'logs':meta.logs(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw['return_data'],'transaction_base64':base64.b64encode(bytes(tx)).decode(),'pool_authority_top_level_signer':False,'signatures_verified':True}

INITIAL_QUOTE=QUOTE
INITIAL_POOL=POOL
INITIAL_POOL_BUMP=POOL_BUMP
def run_case(c,binary=None):
 global QUOTE,POOL,POOL_BUMP
 if c.get('exotic'):
  QUOTE=Pubkey.from_bytes(bytes([81])*32);POOL,POOL_BUMP=Pubkey.find_program_address([b'pool',bytes(2),bytes(POOL_AUTH),bytes(MINT),bytes(QUOTE)],AMM)
  c={**c,'curve_patches':[(83,bytes(QUOTE).hex()),(123,'01')]+c.get('curve_patches',[]),'pump_config_patches':[(1045,'01'),(1046,(2**64-1).to_bytes(8,'little').hex())]+c.get('pump_config_patches',[])}
 try:return run_cto(c,binary)
 finally:QUOTE,POOL,POOL_BUMP=INITIAL_QUOTE,INITIAL_POOL,INITIAL_POOL_BUMP

def cases():
 rows=[]
 def add(label,**c):rows.append({'name':label,**c})
 add('base');add('holder',holder=True,new_none=True);add('existing-cashback',pool_patches=[(244,'01')]);add('holder-converts-cashback',holder=True,new_none=True,pool_patches=[(244,'01')]);add('existing-holder',holder=True,new_none=True,pool_patches=[(270,'01')]);add('holder-immutable',pool_patches=[(270,'01')])
 for off in [8,9,11,43,75,107,139,171,203,211,243,244,245,261,269,270,271,279]:
  width=32 if off in [11,43,75,107,139,171,211] else 16 if off==245 else 8 if off in [203,261,271,279] else 2 if off==9 else 1
  for v in [0,1,2]:add('pool-field-'+str((off,v)),pool_patches=[(off,v.to_bytes(width,'little').hex())])
 for n in [0,7,8,210,211,242,243,244,245,260,261,268,269,270,271,278,279,286,287,301,302]:add('pool-length-'+str(n),pool_length=n)
 for n in [0,1,2000000,2888400,10**9]:
  for size in [211,243,271,287,301]:add('rent-'+str((n,size)),pool_length=size,pool_lamports=n)
 for k in [Pubkey.default(),PUMP,PROGRAM]:add('pool-owner-'+str(k),pool_owner=str(k))
 for off in [0,8,56,907,939,940,941]:add('config-field-'+str(off),config_patches=[(off,'00')])
 for key in ['pool_authority','pump_amm','amm_global_config','pool','pump_amm_event_authority','event_authority']:add('wrong-'+key,wrong=key)
 add('wrong-authority',wrong_authority=True)
 for off,val in [(243,'01'),(270,'01'),(279,'0100000000000000')]:
  add('guards-'+str(off),pool_patches=[(off,val),(11,bytes(AUTH.pubkey()).hex())])
 for fee in [0,1,99,100,101,10000,2**64-1]:
  for maxfee in [0,100,2**64-1]:
   add('fee-'+str((fee,maxfee)),exotic=True,fee_bps=fee,config_patches=[(940,'01'),(941,maxfee.to_bytes(8,'little').hex())])
 for off in [243,244,269,270,279]:add('exotic-field-'+str(off),exotic=True,fee_bps=100,config_patches=[(940,'01'),(941,(100).to_bytes(8,'little').hex())],pool_patches=[(off,'01')])
 add('exotic-config-off',exotic=True,fee_bps=1,config_patches=[(940,'00')])
 add('exotic-holder-cashback',exotic=True,fee_bps=1,holder=True,new_none=True,config_patches=[(940,'01')],pool_patches=[(244,'01')])
 add('exotic-holder',exotic=True,fee_bps=1,holder=True,new_none=True,config_patches=[(940,'01')])
 add('exotic-no-fee',exotic=True,pool_patches=[(269,'01')])
 for q in [Pubkey.default(),INITIAL_QUOTE,Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')]:add('exotic-pool-quote-'+str(q),exotic=True,fee_bps=1,pool_patches=[(75,bytes(q).hex())],config_patches=[(940,'01')])
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,Path(__file__),extra_inputs=AMM_REPORT_INPUTS);a.candidate=a.candidate and pin_program(a.candidate);rows=[];bad=[];reached=0
 for c in cases():
  x=run_case(c);y=run_case(c,a.candidate) if a.candidate else None
  reached+=any('Instruction: AdminCtoPool' in l for l in x['logs'])
  diffs=[k for k in ['error','before','after','events','inner','return'] if x[k]!=y[k]] if y else []
  rows.append({'case':c,'original':x,'candidate':y,'match':not diffs if y else None,'mismatched_fields':diffs})
  if diffs:bad.append(c['name'])
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'scope':'Captured Pump admin_cto invokes AMM admin_cto_pool with genuine CPI PDA signing; top-level signatures are ordinary test-owned keys. Synthetic states and upstream-rejected contexts do not establish all downstream contexts.','original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'candidate_sha256':sha(a.candidate) if a.candidate else None,'script_sha256':sha(Path(__file__)),'case_count':len(rows),'cases_reaching_amm':reached,'mismatches':bad,'cases':rows}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'cases':len(rows),'cases_reaching_amm':reached,'mismatch_count':len(bad),'mismatches':bad[:40]}))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
