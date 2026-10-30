#!/usr/bin/env python3
"""Partial exact-quote v3 recovery with verified signatures and explicit synthetic state."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
import argparse,hashlib,json,struct,gzip,base64
import pump_trade_fixture as f
from pump_amm_reusable_harness import pin_program
program=f.Pubkey.from_string(f.x['program']);user=f.Keypair.from_seed(bytes([231])*32)
initial={key:f.vm.get_account(key) for key in f.msg.account_keys}
curve=f.Pubkey.from_string(f.x['accounts']['curve']);global_key=f.Pubkey.from_string(f.x['accounts']['global']);fee_key=f.Pubkey.from_string(f.x['accounts']['fee_config'])
base_in,base_out=struct.unpack_from('<QQ',initial[curve].data,8)
def run(binary,c):
    vm=f.LiteSVM().with_transaction_history(0)
    for name in ['pump_fees']:
        cap=json.loads((f.R/f'evidence/original/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),f.R/f'evidence/original/{name}/deployed.so')
    for name in ['spl_token','spl_token_2022','associated_token']:
        cap=json.loads((f.R/f'evidence/dependencies/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(cap['program']),f.R/f'evidence/dependencies/{name}/deployed.so')
    for key,account in initial.items():
        if account is not None:vm.set_account(key,account)
    vm.add_program_from_file(program,binary)
    if c.get("user_lamports"):
        account=vm.get_account(user.pubkey());vm.set_account(user.pubkey(),f.Account(c["user_lamports"],account.data,account.owner))
    data=bytearray(initial[curve].data);struct.pack_into('<QQ',data,8,c['reserve_in'],c['reserve_out'])
    if 'real_base' in c:struct.pack_into('<Q',data,24,c['real_base'])
    for offset in c.get('flags',[]):data[offset]=1
    mutation=c.get('mutation','none')
    if mutation=='complete':data[48]=1
    if mutation=='creator_zero':data[49:81]=bytes(32)
    vm.set_account(curve,f.Account(initial[curve].lamports,bytes(data),initial[curve].owner))
    if mutation=='global_discriminator':
        g=initial[global_key];gd=bytearray(g.data);gd[0]^=1;vm.set_account(global_key,f.Account(g.lamports,bytes(gd),g.owner))
    if mutation=='fee_owner':
        account=initial[fee_key];vm.set_account(fee_key,f.Account(account.lamports,account.data,f.Pubkey.default()))
    if mutation=='base_user_wrong_owner':
        key=f.Pubkey.from_string(f.x['accounts']['user_base']);account=initial[key];vm.set_account(key,f.Account(account.lamports,account.data,f.Pubkey.default()))
    if 'fees' in c or mutation=='empty_tiers':
        pb,cb,bb=c.get('fees',[95,30,5000]);account=initial[fee_key];fees=struct.pack('<QQQ',0,pb,cb)
        normal=struct.pack('<I',0) if mutation=='empty_tiers' else struct.pack('<I',1)+bytes(16)+fees
        encoded=account.data[:41]+fees+normal+struct.pack('<I',0)+fees
        vm.set_account(fee_key,f.Account(account.lamports,encoded.ljust(len(account.data),b'\0'),account.owner))
        g=initial[global_key];gd=bytearray(g.data);struct.pack_into('<Q',gd,997,bb);vm.set_account(global_key,f.Account(g.lamports,bytes(gd),g.owner))
    if c.get('distinct_flat'):
        ac=vm.get_account(fee_key);data=bytearray(ac.data);struct.pack_into('<QQQ',data,41,0,1000,500);vm.set_account(fee_key,f.Account(ac.lamports,bytes(data),ac.owner))
    if 'fee_len' in c:
        ac=vm.get_account(fee_key);vm.set_account(fee_key,f.Account(ac.lamports,ac.data[:c['fee_len']].ljust(c['fee_len'],b'\0'),ac.owner))
    if c.get('fee_disc'):
        ac=vm.get_account(fee_key);data=bytearray(ac.data);data[0]^=1;vm.set_account(fee_key,f.Account(ac.lamports,bytes(data),ac.owner))
    ix=f.ixs[-1];metas=list(ix.accounts)
    if mutation=='wrong_buyback':
        key=f.Pubkey(bytes([92])*32);metas[13]=f.AccountMeta(key,False,True);vm.set_account(key,f.Account(10**10,b'',f.Pubkey.default()))
    if mutation=='curve_readonly':metas[5]=f.AccountMeta(curve,False,False)
    if c.get('token_quote'):
        quote=f.Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v');token=f.Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb' if c.get('quote2022') else 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');ata=f.Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
        mint=bytearray(82);struct.pack_into('<Q',mint,36,10**15);mint[44]=6;mint[45]=1;vm.set_account(quote,f.Account(10**9,bytes(mint),token))
        def token_account(authority,amount):
            address=f.Pubkey.find_program_address([bytes(authority),bytes(token),bytes(quote)],ata)[0];data=bytearray(165);data[:32]=bytes(quote);data[32:64]=bytes(authority);struct.pack_into('<Q',data,64,amount);data[108]=1;vm.set_account(address,f.Account(10**9,bytes(data),token));return address
        ca=token_account(curve,10**12);ua=token_account(user.pubkey(),10**12);ba=token_account(metas[13].pubkey,0)
        ac=vm.get_account(curve);data=bytearray(ac.data);data[83:115]=bytes(quote);vm.set_account(curve,f.Account(ac.lamports,bytes(data),ac.owner))
        metas[2]=f.AccountMeta(quote,False,False);metas[4]=f.AccountMeta(token,False,False);metas[7]=f.AccountMeta(ca,False,True);metas[10]=f.AccountMeta(ua,False,True)
        if c.get('insert') is not None:metas.insert(c['insert'],f.AccountMeta(ba,False,True))
        if c.get('replace') is not None:metas[c['replace']]=f.AccountMeta(ba,False,True)
        if 'quote_fees' in c:
            pb,cb,bb=c['quote_fees'];ac=vm.get_account(fee_key);normal=struct.pack('<QQQ',0,95,30);stable=struct.pack('<QQQ',0,pb,cb)
            encoded=ac.data[:41]+normal+struct.pack('<I',1)+bytes(16)+normal+struct.pack('<I',1)+bytes(16)+stable+normal
            vm.set_account(fee_key,f.Account(ac.lamports,encoded.ljust(len(ac.data),b'\0'),ac.owner))
            g=vm.get_account(global_key);gd=bytearray(g.data);struct.pack_into('<Q',gd,997,bb);vm.set_account(global_key,f.Account(g.lamports,bytes(gd),g.owner))
        mutation=c.get('quote_mutation','')
        if mutation=='mint_owner':
            ac=vm.get_account(quote);vm.set_account(quote,f.Account(ac.lamports,ac.data,f.Pubkey.default()))
        if mutation in ['user_authority','curve_authority','buyback_authority','user_mint']:
            key=ua if mutation.startswith('user') else ca if mutation.startswith('curve') else ba
            ac=vm.get_account(key);data=bytearray(ac.data);offset=0 if mutation=='user_mint' else 32;data[offset:offset+32]=bytes([93])*32;vm.set_account(key,f.Account(ac.lamports,bytes(data),ac.owner))
        if mutation in ['user_address','curve_address','buyback_address']:
            index=10 if mutation.startswith('user') else 7 if mutation.startswith('curve') else 13;old=metas[index].pubkey;key=f.Pubkey(bytes([94])*32);vm.set_account(key,vm.get_account(old));metas[index]=f.AccountMeta(key,False,True)
        if mutation=='buyback_wallet':metas[13]=f.ixs[-1].accounts[13]
    trade=f.Instruction(ix.program_id,bytes.fromhex('e1f7501ed5b38488')+struct.pack('<QQ',c['amount'],c['max_cost'])+bytes(c.get('trailing',[])),metas)
    tx=f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],user.pubkey(),[user],vm.latest_blockhash());assert all(tx.verify_with_results());result=vm.send_transaction(tx)
    failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta() if failed else result
    state={}
    for key in set(f.msg.account_keys)|set(m.pubkey for m in metas):
        if key==program:continue # Executable image is deliberately different; compared separately by whole-file build receipt.
        account=vm.get_account(key)
        if account:state[str(key)]={'lamports':account.lamports,'data_sha256':hashlib.sha256(account.data).hexdigest(),'data_hex':None if account.executable else account.data.hex(),'owner':str(account.owner)}
    return {'error':str(result.err()) if failed else None,'accounts':state,'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'event_payloads':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signature_verified':all(tx.verify_with_results()),'return_data':json.loads(meta.to_json()).get('return_data')}
def cases():
 rows=[]
 for amount in [0,1,2,3,4,10,100,1000,1000000,10**9,10**12,2**64-1]:
  for minimum in [0,1,1000000]:rows.append({'amount':amount,'max_cost':minimum})
 for fees in [[0,0,0],[95,0,5000],[0,30,5000],[100,100,5000],[3000,3000,5000],[10000,0,5000],[0,10000,5000],[6000,6000,5000],[10001,0,5000]]:
  for amount in [1,2,10,1000,10**9]:rows.append({'amount':amount,'max_cost':1,'fees':fees})
 for mutation in ['complete','creator_zero','wrong_buyback','empty_tiers','global_discriminator','fee_owner','curve_readonly','base_user_wrong_owner']:
  for amount in [0,10**9]:rows.append({'amount':amount,'max_cost':1,'mutation':mutation})
 for real in [0,1,1000000,10**9]:
  for amount in [1,10**6,10**9]:
   for trailing in [[],[0],[1]]:rows.append({'amount':amount,'max_cost':1,'real_base':real,'trailing':trailing})
 for amount in [10**10,10**11,10**12,10**13]:
  for trailing in [[],[0],[1]]:rows.append({'amount':amount,'max_cost':1,'user_lamports':10**16,'trailing':trailing})
 for flags in [[81],[82],[124],[81,124]]:rows.append({'amount':10**9,'max_cost':1,'flags':flags})
 for length in [0,7,8,64,65,104,112,2511,2512,4072,4073,4096,4097]:rows.append({'amount':10**9,'max_cost':1,'fee_len':length})
 for rin,rout in [(0,1),(1,0),(1,1),(1000,1000),(2**64-1,1),(1,2**64-1),(2**64-1,2**64-1)]:rows.append({'amount':10**9,'max_cost':1,'reserve_in':rin,'reserve_out':rout})
 for token2022 in [False,True]:
  for amount in [0,1,2,3,1000,10**9,10**11]:
   for flags in [[],[81],[124]]:rows.append({'amount':amount,'max_cost':1,'token_quote':True,'quote2022':token2022,'replace':13,'flags':flags})
  for fees in [[0,0,0],[100,100,5000],[1,1,1],[3000,3000,9999]]:rows.append({'amount':10**9,'max_cost':1,'token_quote':True,'quote2022':token2022,'replace':13,'quote_fees':fees})
 for mutation in ['mint_owner','user_authority','curve_authority','buyback_authority','user_mint','user_address','curve_address','buyback_address','buyback_wallet']:
  rows.append({'amount':10**9,'max_cost':1,'token_quote':True,'replace':13,'quote_mutation':mutation})
 for token in [False,True]:
  for trailing in [[],[0],[1]]:
   for minimum in [1,793099000000000,793099000000001,10**15]:
    rows.append({'amount':10**11,'max_cost':minimum,'flags':[81],'trailing':trailing,'user_lamports':10**16,'token_quote':token,'replace':13})
 import random
 rng=random.Random(221026)
 for _ in range(100):
  rows.append({'amount':rng.randrange(1,10**12),'max_cost':rng.choice([1,10**9,10**14]),'fees':[rng.randrange(0,1001),rng.randrange(0,1001),rng.randrange(0,10001)],'user_lamports':10**16,'trailing':[rng.randrange(2)]})
 return [{'reserve_in':base_in,'reserve_out':base_out,**c} for c in rows]
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=f.pathlib.Path);p.add_argument('--output',type=f.pathlib.Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate) if a.candidate else None;rows=[];bad=[];original=pin_program(f.R/'evidence/original/pump/deployed.so')
 for i,c in enumerate(cases()):
  x=run(original,c);y=run(a.candidate,c) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','accounts','inner_instructions','event_payloads','return_data']) if y else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(i)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'scope':'Partial exact-quote v3 SOL and synthetic USDC fixtures; other quote routes, token extensions and full source equivalence are not established. Normal verified transaction signatures.','original_sha256':sha(original),'candidate_sha256':sha(a.candidate) if a.candidate else None,'case_count':len(rows),'cases':rows,'mismatches':bad};raw=(json.dumps(report,separators=(',',':'))+'\n').encode();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(gzip.compress(raw,mtime=0) if a.output.suffix=='.gz' else raw);print(json.dumps({'cases':len(rows),'mismatches':bad}));assert not bad
if __name__=='__main__':main()
