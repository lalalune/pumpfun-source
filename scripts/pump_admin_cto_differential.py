#!/usr/bin/env python3
"""Pump admin_cto reconstruction comparisons with genuine captured dependency CPIs."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_donation_create_differential import *
import pump_validate_admin as pump
import pump_amm_admin_differential as amm
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
IX=next(x for x in pump.IDL['instructions'] if x['name']=='admin_cto')
def ata(owner):return Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
def run(c,binary=None):
 QUOTE=Pubkey.from_string(c.get('quote',str(globals()['QUOTE'])));TOKEN=Pubkey.from_string(c.get('token_program',str(globals()['TOKEN'])));POOL,POOL_BUMP=Pubkey.find_program_address([b'pool',bytes(2),bytes(POOL_AUTH),bytes(MINT),bytes(QUOTE)],AMM)
 def ata(owner):return Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
 vm=LiteSVM().with_transaction_history(0);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('pump',PUMP),('pump_amm',AMM),('pump_fees',PROGRAM)]:vm.add_program_from_file(key,binary if name=='pump' and binary else ROOT/f'evidence/original/{name}/deployed.so')
 for name,key in [('spl_token',globals()['TOKEN']),('spl_token_2022',Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 gd=bytearray(pump.DATA);gd[418:450]=bytes(OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey());
 for off,val in c.get('global_patches',[]):gd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 gd=gd[:c.get('global_length',len(gd))];vm.set_account(pump.GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PUMP)))));vm.set_account(amm.CONFIG_KEY,Account(10**9,bytes(amm.RAW),AMM))
 for mint in [MINT,QUOTE]:
  md=bytearray(82);md[44]=9 if mint==QUOTE else 6;md[45]=1;vm.set_account(mint,Account(10**9,bytes(md),TOKEN))
 sd=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([Pubkey.find_program_address([b'sharing-config',bytes(MINT)],PROGRAM)[1],c.get('version',2),c.get('status',1)])+bytes(MINT)+bytes(AUTH.pubkey())+bytes([c.get('revoked',0)])+(1).to_bytes(4,'little')+bytes(AUTH.pubkey())+(10000).to_bytes(2,'little')
 if 'shareholders' in c:
  sd=sd[:76]+len(c['shareholders']).to_bytes(4,'little')+b''.join(bytes(Pubkey.from_string(key))+bps.to_bytes(2,'little') for key,bps in c['shareholders'])
 sd=bytearray(sd.ljust(1024,b'\0'))
 for off,val in c.get('sharing_patches',[]):sd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 sd=sd[:c.get('sharing_length',len(sd))]
 vm.set_account(SHARING,Account(10**9,bytes(sd),Pubkey.from_string(c.get('sharing_owner',str(PROGRAM)))))
 current=Pubkey.from_string(c.get('current',str(SHARING)))
 cd=bytearray(CURVE_DATA);cd[49:81]=bytes(current);cd[24:32]=(1000).to_bytes(8,'little');cd[48]=c.get('complete',0)
 if c.get('quote'):cd[83:115]=bytes(QUOTE)
 for off,val in c.get('curve_patches',[]):cd[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
 cd=cd[:c.get('curve_length',len(cd))];vm.set_account(CURVE,Account(10**9,bytes(cd),Pubkey.from_string(c.get('curve_owner',str(PUMP)))))
 pd=hashlib.sha256(b'account:Pool').digest()[:8]+bytes([POOL_BUMP])+bytes(2)+bytes(POOL_AUTH)+bytes(MINT)+bytes(QUOTE)+bytes(96)+bytes(8)+bytes(SHARING)+bytes(2)+bytes(16)
 vm.set_account(POOL,Account(10**9,pd.ljust(301,b'\0'),AMM))
 vault=Pubkey.find_program_address([b'creator-vault',bytes(current)],PUMP)[0];holder=Pubkey.find_program_address([b'holder-rewards',bytes(MINT)],PUMP)[0];holdervault=Pubkey.find_program_address([b'creator-vault',bytes(holder)],PUMP)[0];ammvault=Pubkey.find_program_address([b'creator_vault',bytes(current)],AMM)[0]
 for key in [vault,holdervault,ammvault,ata(current),ata(vault),ata(holdervault),ata(ammvault),POOL_AUTH,pump.EVENT,amm.EVENT,EVENT]:vm.set_account(key,Account(0,b'',Pubkey.default()))
 names={'admin_set_creator_authority':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'quote_mint':QUOTE,'quote_token_program':TOKEN,'associated_token_program':ATA,'system_program':Pubkey.default(),'bonding_curve':CURVE,'current_creator':current,'current_creator_quote_token_account':ata(current),'creator_vault':vault,'creator_vault_quote_token_account':ata(vault),'holder_creator_vault':holdervault,'holder_creator_vault_quote_token_account':ata(holdervault),'pump_amm':AMM,'amm_global_config':amm.CONFIG_KEY,'pool_authority':POOL_AUTH,'pool':POOL,'pump_amm_event_authority':amm.EVENT,'coin_creator_vault_authority':ammvault,'coin_creator_vault_ata':ata(ammvault),'sharing_config':SHARING,'pump_fees':PROGRAM,'pump_fees_event_authority':EVENT,'event_authority':pump.EVENT,'program':PUMP}
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False),a.get('writable',False)) for a in IX['accounts']]
 assert not any(m.is_signer and m.pubkey==POOL_AUTH for m in metas)
 for name,patch in c.get('accounts',{}).items():
  key=names[name];old=vm.get_account(key);data=bytearray(old.data if old else b'')
  if 'data' in patch:data=bytearray.fromhex(patch['data'])
  if 'tokens' in patch:
   owners={'current_creator_quote_token_account':current,'creator_vault_quote_token_account':vault,'holder_creator_vault_quote_token_account':holdervault,'coin_creator_vault_ata':ammvault};data=bytearray(165);data[:32]=bytes(QUOTE);data[32:64]=bytes(owners[name]);data[64:72]=patch['tokens'].to_bytes(8,'little');data[108]=1;patch={**patch,'owner':str(TOKEN),'lamports':patch.get('lamports',2039280)}
  for off,val in patch.get('patches',[]):data[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  if 'length' in patch:data=data[:patch['length']]
  vm.set_account(key,Account(patch.get('lamports',old.lamports if old else 0),bytes(data),Pubkey.from_string(patch.get('owner',str(old.owner) if old else str(Pubkey.default()))),patch.get('executable',False)))
 metas=[AccountMeta(m.pubkey,m.is_signer,m.is_writable and IX['accounts'][i]['name'] not in c.get('readonly',[])) for i,m in enumerate(metas)]
 if c.get('current_writable'):metas[8]=AccountMeta(metas[8].pubkey,metas[8].is_signer,True)
 holderarg=b'\0' if 'holder' not in c else bytes([1,int(c['holder'])]);fee=b'\0' if 'fee' not in c else b'\1'+c['fee'].to_bytes(8,'little');new=b'\0' if c.get('new_none') else bytes([1])+bytes(Pubkey.from_string(c.get('new_creator',str(OTHER.pubkey()))))
 if c.get('unsigned'):metas=[AccountMeta(m.pubkey,False,m.is_writable) for m in metas]
 if 'count' in c:metas=metas[:c['count']]
 signers=[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else [])
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,bytes(IX['discriminator'])+holderarg+fee+new+bytes.fromhex(c.get('trailing','')),metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for name,key in {**names,'transaction_payer':PAYER.pubkey()}.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   out[name]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;raw=json.loads(meta.to_json())
 return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'logs':meta.logs(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw['return_data'],'transaction_base64':base64.b64encode(bytes(tx)).decode(),'pool_authority_top_level_signer':False,'signatures_verified':True}
def inherited_cases():
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
def cases():
 rows=inherited_cases()
 rows += [{'name':'fee-'+str(n),'fee':n} for n in [0,1,10,100,999,1000,10000,10001,65535,2**64-1]]
 rows += [{'name':'curve-length-'+str(n),'curve_length':n} for n in [0,7,8,48,49,80,81,82,83,114,115,122,123,124,125,133,141,166]]
 rows += [{'name':'curve-bool-'+str(n),'curve_patches':[(n,'02')]} for n in [48,81,82,123,124]]
 rows += [{'name':'curve-byte-'+str(n),'curve_patches':[(n,'ff')]} for n in [0,8,49,83,115]]
 rows += [{'name':'global-length-'+str(n),'global_length':n} for n in [0,7,8,417,418,449,450,512]]
 rows += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in IX['accounts'] if a['name'] not in ['admin_set_creator_authority','pool_authority','pump_fees_event_authority','pump_fees','event_authority','sharing_config']]
 rows += [{'name':'readonly-'+a['name'],'readonly':[a['name']]} for a in IX['accounts'] if a.get('writable')]
 rows += [{'name':'owner-'+kind+'-'+name,kind+'_owner':str(key)} for kind in ['global','curve'] for name,key in [('system',Pubkey.default()),('fees',PROGRAM)]]
 rows += [{'name':'complete-'+str(n),'complete':n} for n in [0,1,2]]
 rows += [{'name':'wallet-'+str(w)+'-'+str(amt),'current':str(OTHER.pubkey()),'current_writable':w,'accounts':{'creator_vault':{'lamports':amt}}} for w in [False,True] for amt in [0,890880,890881,1000000]]
 rows += [{'name':'holder-sweep-'+str(amt),'holder':True,'new_none':True,'accounts':{'creator_vault':{'lamports':amt}}} for amt in [0,890880,890881,1000000]]
 rows += [{'name':'stable-'+str(i),'quote':str(Pubkey.from_bytes(bytes([88])*32)),**v} for i,v in enumerate([{}, {'fee':0},{'fee':1},{'fee':10000},{'fee':10001},{'fee':2**64-1},{'holder':True,'new_none':True},{'holder':True,'new_none':True,'accounts':{'creator_vault_quote_token_account':{'tokens':1000}}},{'current':str(OTHER.pubkey()),'current_writable':True,'accounts':{'creator_vault_quote_token_account':{'tokens':1000}}}])]
 rows += [{'name':'count-'+str(i),'count':i} for i in range(len(IX['accounts']))]+[{'name':'unsigned','unsigned':True},{'name':'trailing','trailing':'ffff'}]
 rows += [{'name':'curve-state-'+str(off)+'-'+str(v),'curve_patches':[(off,bytes([v]).hex())]} for off in [81,82,123,124] for v in [0,1]]
 rows += [{'name':'holder-options-'+str(old)+'-'+str(h)+'-'+str(n),'curve_patches':[(124,bytes([old]).hex())],'new_none':n,**({} if h is None else {'holder':h})} for old in [0,1] for h in [None,False,True] for n in [False,True]]
 rows += [{'name':'account-layout-'+name+'-'+str(i),'accounts':{name:patch}} for name in ['mint','quote_mint','quote_token_program','pool','amm_global_config','current_creator','creator_vault','holder_creator_vault','coin_creator_vault_authority'] for i,patch in enumerate([{'length':0},{'lamports':0},{'owner':str(Pubkey.default())},{'data':'00'},{'lamports':1000000}])]
 rows += [{'name':'pool-byte-'+str(off),'accounts':{'pool':{'patches':[(off,'ff')]}}} for off in [0,8,9,11,43,75,211,243,244]]
 rows += [{'name':'amm-funds-'+str(h)+'-'+str(amount),'holder':h,'new_none':h,'current':str(OTHER.pubkey()),'current_writable':True,'accounts':{'coin_creator_vault_ata':{'tokens':amount}}} for h in [False,True] for amount in [0,1,1000000]]
 rows += [{'name':'stable-fee-'+str(n),'quote':str(Pubkey.from_bytes(bytes([88])*32)),'fee':n} for n in [1,50,100,999,1000,1001]]
 rows += [{'name':'token22-'+str(i),'token_program':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','quote':str(Pubkey.from_bytes(bytes([88])*32)),**v} for i,v in enumerate([{}, {'holder':True,'new_none':True,'accounts':{'creator_vault_quote_token_account':{'tokens':1000}}},{'current':str(OTHER.pubkey()),'current_writable':True,'accounts':{'creator_vault_quote_token_account':{'tokens':1000}}}])]
 rows += [{'name':'shared-amm-'+str(h)+'-'+str(amount),'holder':h,'new_none':h,'accounts':{'coin_creator_vault_ata':{'tokens':amount}}} for h in [False,True] for amount in [0,1,1000000]]
 rows += [{'name':'source-shape-'+name+'-'+str(i),'current':str(OTHER.pubkey()),'current_writable':True,'quote':str(Pubkey.from_bytes(bytes([88])*32)),'accounts':{name:v}} for name in ['creator_vault_quote_token_account','coin_creator_vault_ata'] for i,v in enumerate([{'data':'00','lamports':2039280,'owner':str(TOKEN)},{'tokens':0},{'tokens':1},{'tokens':1,'patches':[(108,'00')]},{'tokens':1,'patches':[(108,'02')]},{'tokens':1,'patches':[(0,bytes(32).hex())]},{'tokens':1,'patches':[(32,bytes(32).hex())]},{'tokens':0,'patches':[(108,'02')]}])]
 rows += [{'name':'quote-global-'+str(i),'quote':str(Pubkey.from_bytes(bytes([88])*32)),'fee':100,**v} for i,v in enumerate([{'global_patches':[(1045,'00')]},{'global_patches':[(1046,(0).to_bytes(8,'little').hex())]},{'global_patches':[(1046,(100).to_bytes(8,'little').hex())]},{'global_patches':[(1013,bytes([88]*32).hex())]}])]
 rows += [{'name':'resize-rent-'+str(size)+'-'+str(balance),'curve_length':size,'accounts':{'bonding_curve':{'lamports':balance}}} for size in [81,125,166,200] for balance in [1,1000000,2046240]]
 rows += [{'name':'paired-'+str(i),**v} for i,v in enumerate([{'curve_patches':[(81,'01')],'holder':True},{'curve_patches':[(124,'01')],'new_creator':str(Pubkey.default())},{'new_none':True,'fee':0},{'holder':True,'fee':0},{'curve_patches':[(81,'01')],'wrong_authority':True},{'curve_length':81,'new_none':True,'accounts':{'bonding_curve':{'lamports':1}}},{'current':str(OTHER.pubkey()),'current_writable':False,'new_none':True}])]
 rows += [{'name':'holder-amm-transfer-'+str(stable)+'-'+str(amount),'holder':True,'new_none':True,**({'quote':str(Pubkey.from_bytes(bytes([88])*32))} if stable else {}),'accounts':{'coin_creator_vault_ata':{'tokens':amount,'lamports':5000000},'creator_vault':{'lamports':1000000},**({'creator_vault_quote_token_account':{'tokens':111}} if stable else {})}} for stable in [False,True] for amount in [0,1,1000000]]
 rows += [{'name':'token-dest-'+str(h)+'-'+str(i),'quote':str(Pubkey.from_bytes(bytes([88])*32)),'holder':h,'new_none':h,**({} if h else {'current':str(OTHER.pubkey()),'current_writable':True}),'accounts':{'creator_vault_quote_token_account':{'tokens':100},('holder_creator_vault_quote_token_account' if h else 'current_creator_quote_token_account'):p}} for h in [False,True] for i,p in enumerate([{'tokens':0},{'tokens':100},{'tokens':0,'patches':[(108,'02')]},{'tokens':0,'patches':[(32,bytes(32).hex())]}])]
 rows += [{'name':'current-kind-'+str(i),'current':str(OTHER.pubkey()),'accounts':{'current_creator':p,'creator_vault':{'lamports':1000000}}} for i,p in enumerate([{'owner':str(PROGRAM)},{'owner':str(PUMP)},{'data':'00'}])]
 rows += [{'name':'current-zero','current':str(Pubkey.default()),'new_none':False}]
 rows += [{'name':'frozen-wallet-'+str(stable)+'-'+source+'-'+str(bad),'current':str(OTHER.pubkey()),'current_writable':True,**({'quote':str(Pubkey.from_bytes(bytes([88])*32))} if stable else {}),'accounts':{'current_creator_quote_token_account':{'tokens':0,'patches':[(108,'02')]},'creator_vault':{'lamports':1000000},source:({'data':'00','lamports':2039280,'owner':str(TOKEN)} if bad else {'tokens':100})}} for stable in [False,True] for source in ['creator_vault_quote_token_account','coin_creator_vault_ata'] for bad in [False,True]]
 rows += [{'name':'fee-boundary-'+str(n),'quote':str(Pubkey.from_bytes(bytes([88])*32)),'fee':n} for n in [299,300,301]]
 rows += [{'name':'holder-disabled-'+str(i),'global_patches':[(1086,'00')],**v} for i,v in enumerate([{}, {'holder':True,'new_none':True},{'holder':True},{'curve_patches':[(124,'01')],'holder':True,'new_none':True}])]
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 paths=[Path(__file__),ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/original/pump_fees/deployed.so',ROOT/'evidence/original/pump_amm/deployed.so']+[ROOT/f'evidence/dependencies/{n}/deployed.so' for n in ['spl_token','spl_token_2022','associated_token']]+[ROOT/'scripts'/n for n in ['fees_donation_create_differential.py','fees_admin_differential.py','pump_validate_admin.py','pump_amm_admin_differential.py']]+[ROOT/f'evidence/upstream/{n}.json' for n in ['pump','pump_fees','pump_amm']]
 if a.candidate:paths.append(a.candidate)
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 original=ROOT/'evidence/original/pump/deployed.so'
 report={'scope':'Signed synthetic captured Pump admin_cto calling Fees by genuine CPI. Pool authority nonsigner at transaction boundary; no privileged signer injection. Not full program identity.','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest() if a.candidate else None,'provenance':hashes,'case_count':len(rows),'cases':rows,'mismatches':bad}
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items()),'Input changed during run'
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
