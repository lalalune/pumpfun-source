if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,hashlib,base64,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_donation_create_differential import *
from pump_amm_reusable_harness import pin_program
from solders.compute_budget import set_compute_unit_limit
import pump_validate_admin as pump
IX=next(x for x in IDL['instructions'] if x['name']=='create_fee_sharing_config')
def run(c,binary=None):
 vm=LiteSVM();vm.add_program_from_file(PROGRAM,pin_program(binary) if binary else ROOT/'evidence/original/pump_fees/deployed.so');vm.add_program_from_file(PUMP,ROOT/'evidence/original/pump/deployed.so');vm.add_program_from_file(AMM,ROOT/'evidence/original/pump_amm/deployed.so')
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 gd=bytearray(pump.DATA);gd[9:41]=bytes(AUTH.pubkey())
 for offset,value in c.get('global_patches',[]):gd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 gd=gd[:c.get('global_length',len(gd))]
 vm.set_account(pump.GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PUMP)))))
 md=bytearray(82);md[44]=6;md[45]=c.get('mint_initialized',1);md=(md+bytearray(max(0,c.get('mint_length',82)-82)))[:c.get('mint_length',82)];vm.set_account(MINT,Account(10**9,bytes(md),Pubkey.from_string(c.get('mint_owner','TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'))))
 cd=bytearray(CURVE_DATA);cd[49:81]=bytes(AUTH.pubkey());cd[48]=c.get('complete',0);cd[24:32]=c.get('tokens',1000).to_bytes(8,'little')
 for offset,value in c.get('curve_patches',[]):cd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 cd=cd[:c.get('curve_length',len(cd))]
 vm.set_account(CURVE,Account(10**9,bytes(cd),Pubkey.from_string(c.get('curve_owner',str(PUMP)))));vm.set_account(SHARING,Account(c.get('prefund',0),b'',Pubkey.default()))
 if c.get('existing'):
  sd=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([Pubkey.find_program_address([b'sharing-config',bytes(MINT)],PROGRAM)[1],c.get('version',1),c.get('status',1)])+bytes(MINT)+bytes(AUTH.pubkey())+bytes([0])+bytes(4)
  sd=bytearray(sd.ljust(c.get('allocation',1024),b'\0'))
  for offset,value in c.get('sharing_patches',[]):sd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  vm.set_account(SHARING,Account(10**9,bytes(sd),PROGRAM))
 names={'event_authority':EVENT,'program':PROGRAM,'payer':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'sharing_config':SHARING,'system_program':Pubkey.default(),'bonding_curve':CURVE,'pump_program':PUMP,'pump_event_authority':pump.EVENT,'pool':PROGRAM,'pump_amm_program':PROGRAM,'pump_amm_event_authority':PROGRAM}
 if c.get('pool'):
  pd=hashlib.sha256(b'account:Pool').digest()[:8]+bytes([POOL_BUMP])+bytes(2)+bytes(POOL_AUTH)+bytes(MINT)+bytes(QUOTE)+bytes(96)+bytes(8)+bytes(AUTH.pubkey())+bytes(2)+bytes(16)
  pd=bytearray(pd)
  for offset,value in c.get('pool_patches',[]):pd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  pd=(pd+bytearray(max(0,c.get('pool_length',len(pd))-len(pd))))[:c.get('pool_length',len(pd))]
  vm.set_account(POOL,Account(10**9,bytes(pd),Pubkey.from_string(c.get('pool_owner',str(AMM)))));names['pool']=POOL;names['pump_amm_program']=AMM;names['pump_amm_event_authority']=Pubkey.find_program_address([b'__event_authority'],AMM)[0]
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and names[a['name']]!=PROGRAM and a['name']!=c.get('readonly')) for a in IX['accounts']]
 metas=metas[:c.get('account_count',len(metas))]
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PROGRAM,bytes(IX['discriminator']),metas)],PAYER.pubkey(),[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else []),vm.latest_blockhash());assert all(tx.verify_with_results());r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r
 return {'case':c,'error':str(r.err()) if failed else None,'logs':m.logs(),'sharing':vm.get_account(SHARING).data.hex() if vm.get_account(SHARING) else None,'inner':json.loads(m.to_json())['inner_instructions'],'transaction_base64':base64.b64encode(bytes(tx)).decode(),'events':[l for l in m.logs() if l.startswith('Program data:')],'curve':vm.get_account(CURVE).data.hex(),'payer_lamports':vm.get_account(PAYER.pubkey()).lamports,'authority_lamports':vm.get_account(AUTH.pubkey()).lamports,'sharing_lamports':vm.get_account(SHARING).lamports if vm.get_account(SHARING) else None,'pool':vm.get_account(POOL).data.hex() if vm.get_account(POOL) else None,'pool_lamports':vm.get_account(POOL).lamports if vm.get_account(POOL) else None,'curve_lamports':vm.get_account(CURVE).lamports}
def cases():
 out=[{'name':'base'},{'name':'graduated-missing','tokens':0},{'name':'graduated','tokens':0,'pool':True},{'name':'incomplete-with-pool','pool':True},{'name':'complete','complete':1},{'name':'existing','existing':True},{'name':'existing-short','existing':True,'allocation':400}]
 out += [{'name':'existing-version-'+str(n),'existing':True,'version':n} for n in [0,1,2,255]]
 out += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in IX['accounts'] if a['name'] not in ['payer','pool','pump_amm_program','pump_amm_event_authority']]
 out += [{'name':'unsigned','unsigned':True}]
 out += [{'name':'curve-'+str(n),'curve_length':n} for n in [0,7,8,48,49,81,82,83,150,166,200]]
 out += [{'name':'creator-'+str(i),'curve_patches':[(49,v.hex())]} for i,v in enumerate([bytes(32),bytes(OTHER.pubkey()),bytes(SHARING)])]
 out += [{'name':'global-length-'+str(n),'global_length':n} for n in [0,7,8,40,739,740,741,1024]]
 for label,creator in [('zero',Pubkey.default()),('other',OTHER.pubkey())]:
  out.append({'name':'graduated-curve-'+label,'tokens':0,'pool':True,'curve_patches':[(49,bytes(creator).hex())]})
  out.append({'name':'graduated-pool-'+label,'tokens':0,'pool':True,'pool_patches':[(211,bytes(creator).hex())]})
 out += [{'name':'prefund-'+str(n),'prefund':n} for n in [1,10**9]]
 out += [{'name':'mint-length-'+str(n),'mint_length':n} for n in [0,7,81,82,83]]
 out += [{'name':'mint-token22','mint_owner':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'},{'name':'mint-uninitialized','mint_initialized':0}]
 out += [{'name':'readonly-'+a['name'],'readonly':a['name'],'tokens':0,'pool':True} for a in IX['accounts'] if a.get('writable')]
 out += [{'name':'account-count-'+str(n),'account_count':n} for n in range(len(IX['accounts']))]
 out += [{'name':'pool-length-'+str(n),'tokens':0,'pool':True,'pool_length':n} for n in [0,7,8,42,74,106,210,211,242,243,244,245,260,261,300]]
 out += [{'name':'pool-patch-'+str(n),'tokens':0,'pool':True,'pool_patches':[(n,'00')]} for n in [0,8,9,11,43,75,211]]
 out += [{'name':'pool-wrong-owner','tokens':0,'pool':True,'pool_owner':str(PUMP)}]
 out += [{'name':'curve-bool-'+str(n)+'-'+str(v),'curve_patches':[(n,bytes([v]).hex())]} for n in [48,81] for v in [0,1,2,255]]
 out += [{'name':'sharing-status-'+str(n),'existing':True,'status':n} for n in [0,1,2,255]]
 out += [{'name':'sharing-patch-'+str(n),'existing':True,'sharing_patches':[(n,'00')]} for n in [0,8,11,43,75,76]]
 out += [{'name':'existing-curve-creator','existing':True,'curve_patches':[(49,bytes(OTHER.pubkey()).hex())]},{'name':'existing-graduated-no-pool','existing':True,'tokens':0}]
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','sharing','curve','payer_lamports','authority_lamports','sharing_lamports','pool','pool_lamports','curve_lamports','events','inner']) if y else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'original_sha256':hashlib.sha256((ROOT/'evidence/original/pump_fees/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'scope':'Synthetic signed local sharing creation using captured Pump/AMM dependencies; no fullbyte identity claim.','cases':rows,'mismatches':bad};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
