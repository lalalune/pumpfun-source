#!/usr/bin/env python3
"""Normally signed local Pump admin_cto invoking captured Fees through real CPI."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_donation_create_differential import *
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
import pump_validate_admin as pump
import pump_amm_admin_differential as amm
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
IX=next(x for x in pump.IDL['instructions'] if x['name']=='admin_cto')
def ata(owner):return Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
def run(c,binary=None):
 vm=LiteSVM().with_transaction_history(0);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('pump',PUMP),('pump_amm',AMM),('pump_fees',PROGRAM)]:vm.add_program_from_file(key,pin_program(binary) if name=='pump_fees' and binary else ROOT/f'evidence/original/{name}/deployed.so')
 for name,key in [('spl_token',TOKEN),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 gd=bytearray(pump.DATA);gd[418:450]=bytes(OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey());vm.set_account(pump.GLOBAL,Account(10**9,bytes(gd),PUMP));vm.set_account(amm.CONFIG_KEY,Account(10**9,bytes(amm.RAW),AMM))
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
 cd=bytearray(CURVE_DATA);cd[49:81]=bytes(current);cd[24:32]=(1000).to_bytes(8,'little');cd[48]=c.get('complete',0)
 for off,val in c.get('curve_patches',[]):cd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 vm.set_account(CURVE,Account(10**9,bytes(cd),PUMP))
 pd=hashlib.sha256(b'account:Pool').digest()[:8]+bytes([POOL_BUMP])+bytes(2)+bytes(POOL_AUTH)+bytes(MINT)+bytes(QUOTE)+bytes(96)+bytes(8)+bytes(SHARING)+bytes(2)+bytes(16)
 vm.set_account(POOL,Account(10**9,pd.ljust(301,b'\0'),AMM))
 vault=Pubkey.find_program_address([b'creator-vault',bytes(current)],PUMP)[0];holder=Pubkey.find_program_address([b'holder-rewards',bytes(MINT)],PUMP)[0];holdervault=Pubkey.find_program_address([b'creator-vault',bytes(holder)],PUMP)[0];ammvault=Pubkey.find_program_address([b'creator_vault',bytes(current)],AMM)[0]
 for key in [vault,holdervault,ammvault,ata(current),ata(vault),ata(holdervault),ata(ammvault),POOL_AUTH,pump.EVENT,amm.EVENT,EVENT]:vm.set_account(key,Account(0,b'',Pubkey.default()))
 names={'admin_set_creator_authority':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'quote_mint':QUOTE,'quote_token_program':TOKEN,'associated_token_program':ATA,'system_program':Pubkey.default(),'bonding_curve':CURVE,'current_creator':current,'current_creator_quote_token_account':ata(current),'creator_vault':vault,'creator_vault_quote_token_account':ata(vault),'holder_creator_vault':holdervault,'holder_creator_vault_quote_token_account':ata(holdervault),'pump_amm':AMM,'amm_global_config':amm.CONFIG_KEY,'pool_authority':POOL_AUTH,'pool':POOL,'pump_amm_event_authority':amm.EVENT,'coin_creator_vault_authority':ammvault,'coin_creator_vault_ata':ata(ammvault),'sharing_config':SHARING,'pump_fees':PROGRAM,'pump_fees_event_authority':EVENT,'event_authority':pump.EVENT,'program':PUMP}
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False),a.get('writable',False)) for a in IX['accounts']]
 assert not any(m.is_signer and m.pubkey==POOL_AUTH for m in metas)
 holderarg=b'\0' if 'holder' not in c else bytes([1,int(c['holder'])]);fee=b'\0';new=b'\0' if c.get('new_none') else bytes([1])+bytes(Pubkey.from_string(c.get('new_creator',str(OTHER.pubkey()))))
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
def cases():
 rows=[{'name':'base'},{'name':'no-new','new_none':True},{'name':'holder-none','holder':True,'new_none':True},{'name':'holder-new','holder':True},{'name':'nonholder-new','holder':False},{'name':'wrong-authority','wrong_authority':True}]
 rows += [{'name':'version-'+str(n),'version':n} for n in [0,1,2,3,255]]
 rows += [{'name':'status-'+str(n),'status':n} for n in [0,1,2,255]]
 rows += [{'name':'revoked-'+str(n),'revoked':n} for n in [0,1,2]]
 rows += [{'name':'patch-'+str(n),'sharing_patches':[(n,'00')]} for n in [0,8,11,43,75,76]]
 rows += [{'name':'holder-version-'+str(n),'holder':True,'new_none':True,'version':n} for n in [0,1,2,255]]
 rows += [{'name':'holder-revoked','holder':True,'new_none':True,'revoked':1},{'name':'holder-paused','holder':True,'new_none':True,'status':0}]
 rows += [{'name':'shares-empty','shareholders':[]},{'name':'shares-multiple','shareholders':[(str(AUTH.pubkey()),5000),(str(OTHER.pubkey()),5000)]}]
 rows += [{'name':'new-'+label,'new_creator':str(key)} for label,key in [('zero',Pubkey.default()),('self',SHARING),('old-admin',AUTH.pubkey()),('program',PROGRAM)]]
 rows += [{'name':'wrong-'+key,'wrong':key} for key in ['pool_authority','pump_fees_event_authority','pump_fees','event_authority','sharing_config']]
 rows += [{'name':'length-'+str(n),'sharing_length':n} for n in [0,7,8,10,11,43,75,76,79,80,113,114,256,1024]]
 rows += [{'name':'owner-system','sharing_owner':str(Pubkey.default())},{'name':'owner-pump','sharing_owner':str(PUMP)},{'name':'empty-small-grow','shareholders':[],'sharing_length':80},{'name':'holder-empty-small','shareholders':[],'sharing_length':80,'holder':True,'new_none':True},{'name':'bad-weight','shareholders':[(str(AUTH.pubkey()),65535)]},{'name':'many-shareholders','shareholders':[(str(Pubkey.from_bytes(bytes([i])*32)),i) for i in range(10,30)]}]
 rows += [{'name':'holder-shares-multiple','holder':True,'new_none':True,'shareholders':[(str(AUTH.pubkey()),5000),(str(OTHER.pubkey()),5000)]},{'name':'paused-revoked-version0','status':0,'revoked':1,'version':0}]
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 original=ROOT/'evidence/original/pump_fees/deployed.so'
 report={'scope':'Signed synthetic captured Pump admin_cto calling Fees by genuine CPI. Pool authority nonsigner at transaction boundary; no privileged signer injection. Not full program identity.','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad}
 publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
