#!/usr/bin/env python3
"""Signed synthetic local probes of original social-fee creation; no source claim."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,pathlib,json,hashlib,base64,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from fees_admin_differential import *
from pump_differential_output import PumpReport
from solders.clock import Clock
IX=next(x for x in IDL['instructions'] if x['name']=='create_social_fee_pda')
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'

def run(c,image):
 vm=LiteSVM().with_transaction_history(0);vm.add_program(PROGRAM,image);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for kp in [AUTH,OTHER,PAYER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 user=c.get('user','1234567890');raw=user.encode();platform=c.get('platform',1)
 seeds=[b'social-fee-pda',raw,bytes([platform])]
 if c.get('order')=='platform-first':seeds=[b'social-fee-pda',bytes([platform]),raw]
 if len(raw)>32:key,bump=OTHER.pubkey(),0
 else:key,bump=Pubkey.find_program_address(seeds,PROGRAM)
 gd=bytearray(BASE);gd[41]=c.get('flags',0)
 for offset,value in c.get('global_patches',[]):gd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 gd=gd[:c.get('global_length',len(gd))]
 vm.set_account(GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PROGRAM)))));vm.set_account(EVENT,Account(0,b'',Pubkey.default()))
 vm.set_account(key,Account(c.get('prefund',0),b'',Pubkey.default()))
 if c.get('existing'):
  state=hashlib.sha256(b'account:SocialFeePda').digest()[:8]+bytes([bump,c.get('version',1)])+len(raw).to_bytes(4,'little')+raw+bytes([platform])+(42).to_bytes(8,'little')*3+bytes([55])*120
  state=bytearray(state.ljust(179,b'\0'))
  for offset,value in c.get('patches',[]):state[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  size=c.get('state_length',len(state));state=(state+bytes(max(0,size-len(state))))[:size]
  vm.set_account(key,Account(10**9,bytes(state),Pubkey.from_string(c.get('state_owner',str(PROGRAM)))))
 names={'payer':AUTH.pubkey(),'social_fee_pda':key,'system_program':Pubkey.default(),'fee_program_global':GLOBAL,'event_authority':EVENT,'program':PROGRAM}
 if c.get('wrong_account'):names[c['wrong_account']]=OTHER.pubkey()
 metas=[AccountMeta(names[x['name']],x.get('signer',False) and not c.get('unsigned'),x.get('writable',False) and x['name']!=c.get('readonly')) for x in IX['accounts']]
 metas=metas[:c.get('account_count',len(metas))]
 payload=bytes(IX['discriminator'])+len(raw).to_bytes(4,'little')+raw+bytes([platform])
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else []),vm.latest_blockhash());assert all(tx.verify_with_results())
 r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;a=vm.get_account(key)
 return {'case':c,'address':str(key),'bump':bump,'error':str(r.err()) if failed else None,'logs':m.logs(),'inner':json.loads(m.to_json())['inner_instructions'],'data':a.data.hex() if a else None,'lamports':a.lamports if a else None,'owner':str(a.owner) if a else None,'authority_lamports':vm.get_account(AUTH.pubkey()).lamports,'transaction_base64':base64.b64encode(bytes(tx)).decode()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,default=ROOT/'work/fees-social-recovery/create-probes.json');a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__)
 cases=[{'name':'base'},{'name':'other-order','order':'platform-first'}]
 cases += [{'name':'platform-'+str(n),'platform':n} for n in range(256)]
 cases += [{'name':'user-'+repr(u),'user':u} for u in ['', '0','00','01','-1','+1',' 1','1 ','a','1a','18446744073709551615','18446744073709551616','9'*20,'1'*21,'1'*32,'1'*33,'é'*10,'😀'*5,'\x00']]
 cases += [{'name':'flags-'+str(n),'flags':n} for n in range(256)]
 cases += [{'name':'existing-'+str(n),'existing':True,'version':n} for n in [0,1,2,255]]
 cases += [{'name':'existing-disabled','existing':True,'flags':1}]
 cases += [{'name':'user-overlong-disabled','user':'1'*21,'flags':1},{'name':'multibyte-overlong','user':'é'*11}]
 cases += [{'name':'prefund-'+str(n),'prefund':n} for n in [1,10**9]]
 cases += [{'name':'wrong-'+x['name'],'wrong_account':x['name']} for x in IX['accounts'] if x['name']!='payer']
 cases += [{'name':'unsigned','unsigned':True}]
 cases += [{'name':'readonly-'+x['name'],'readonly':x['name']} for x in IX['accounts'] if x.get('writable')]
 cases += [{'name':'accounts-'+str(n),'account_count':n} for n in range(len(IX['accounts']))]
 cases += [{'name':'global-patch-'+str(n),'global_patches':[(n,'00')]} for n in [0,8]]
 cases += [{'name':'global-length-'+str(n),'global_length':n} for n in [0,7,8,9,41,42,74,82,337]]
 cases += [{'name':'state-length-'+str(n),'existing':True,'state_length':n} for n in [0,7,8,9,10,14,24,25,49,168,169,178,179,180,256]]
 cases += [{'name':'state-patch-'+str(n),'existing':True,'patches':[(n,'00')]} for n in [0,8,14,24]]
 cases += [{'name':'global-owner','global_owner':str(Pubkey.default())},{'name':'state-owner','existing':True,'state_owner':str(Pubkey.default())}]
 rows=[];failures=[]
 # Read each image once, so every case and the receipt use the same bytes.
 original=ORIGINAL.read_bytes();candidate=a.candidate.read_bytes() if a.candidate else None
 for c in cases:
  x=run(c,original);y=run(c,candidate) if a.candidate else None
  keys=['error','data','lamports','owner','authority_lamports','inner']
  match=all(x[k]==y[k] for k in keys) and [l for l in x['logs'] if l.startswith('Program data:')]==[l for l in y['logs'] if l.startswith('Program data:')] if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 publisher.write((json.dumps({'original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest() if a.candidate else None,'scope':'Normally signed synthetic local creation cases; no full-program or byte identity claim.','cases':rows,'mismatches':failures},indent=2)+'\n').encode('utf-8'))
 print('cases',len(rows),'mismatches',failures)
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
