#!/usr/bin/env python3
"""Compare the partial USDC-quote buy/sell-v3 SBF paths with the captured original."""
import argparse, hashlib, json, struct
import pump_trade_fixture as f
from pump_amm_reusable_harness import pin_program
p=argparse.ArgumentParser();p.add_argument('--candidate',type=f.pathlib.Path,required=True);p.add_argument('--source-directory',type=f.pathlib.Path,default=f.R/'programs/pump');p.add_argument('--output',type=f.pathlib.Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate)
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
    data=bytearray(initial[curve].data);struct.pack_into('<QQ',data,8,c['reserve_in'],c['reserve_out'])
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
    if 'fee_len' in c:
        ac=vm.get_account(fee_key);vm.set_account(fee_key,f.Account(ac.lamports,ac.data[:c['fee_len']].ljust(c['fee_len'],b'\0'),ac.owner))
    ix=f.ixs[-1];metas=list(ix.accounts)
    if mutation=='wrong_buyback':
        key=f.Pubkey(bytes([92])*32);metas[13]=f.AccountMeta(key,False,True);vm.set_account(key,f.Account(10**10,b'',f.Pubkey.default()))
    if mutation=='curve_readonly':metas[5]=f.AccountMeta(curve,False,False)
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
    trade=f.Instruction(ix.program_id,(bytes.fromhex('07051dc4f5176550') if c['kind']=='buy' else ix.data[:8])+struct.pack('<QQ',c['amount'],c['min_output']),metas)
    result=vm.send_transaction(f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],user.pubkey(),[user],vm.latest_blockhash()))
    failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta() if failed else result
    state={}
    for key in set(f.msg.account_keys)|set(m.pubkey for m in metas):
        if key==program:continue # Executable image is deliberately different; compared separately by whole-file build receipt.
        account=vm.get_account(key)
        if account:state[str(key)]={'lamports':account.lamports,'data_sha256':hashlib.sha256(account.data).hexdigest(),'owner':str(account.owner)}
    return {'error':str(result.err()) if failed else None,'accounts':state,'event_payloads':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}






cases=[]
for kind in ['buy','sell']:
 for flags in [[],[81],[124],[81,124]]:
  for amount in [1,1000,35767,1000000,500000000,1000000000]:
   for quote2022 in [False,True]:
    cases.append({'kind':kind,'amount':amount,'min_output':10**12 if kind=='buy' else 0,'reserve_in':base_in,'reserve_out':base_out,'replace':13,'flags':flags,'quote2022':quote2022})
 for flags in [[],[81]]:
  for fees in [[0,0,0],[100,100,5000],[1,1,1],[3000,3000,9999]]:
   cases.append({'kind':kind,'amount':500000000,'min_output':10**12 if kind=='buy' else 0,'reserve_in':base_in,'reserve_out':base_out,'replace':13,'flags':flags,'quote_fees':fees})
for kind in ['buy','sell']:
 for mutation in ['mint_owner','user_authority','curve_authority','buyback_authority','user_mint','user_address','curve_address','buyback_address','buyback_wallet']:
  cases.append({'kind':kind,'amount':500000000,'min_output':10**12 if kind=='buy' else 0,'reserve_in':base_in,'reserve_out':base_out,'replace':13,'quote_mutation':mutation})
rows=[]
for c in cases:
 o=run(f.R/'evidence/original/pump/deployed.so',c);n=run(a.candidate,c);fields=['error','accounts','event_payloads','inner'];different=[key for key in fields if o[key]!=n[key]]
 rows.append({'case':c,'different_fields':different,'original':o,'candidate':n})
fails=[i for i,r in enumerate(rows) if r['different_fields']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={str(p.relative_to(a.source_directory)):sha(p) for p in sorted(a.source_directory.rglob('*')) if p.is_file() and 'target' not in p.parts and (p.suffix=='.rs' or p.name in ['Cargo.toml','Cargo.lock'])}
report={'scope':'Partial USDC-quote buy_v3/sell_v3 reconstruction: local synthetic quote mint/token accounts layered on saved Pump fixture, not captured real USDC account state. Tests SPL Token and Token2022 ownership variants without extensions, fees, flags and account guards. Compares all nonexecutecutable account state, errors, raw events and full inner instructions. Other quote routes and complete program byte identity remain unproven.','candidate_sha256':sha(a.candidate),'original_sha256':sha(f.R/'evidence/original/pump/deployed.so'),'source_sha256':sources,'cases':rows,'case_count':len(rows),'mismatches':fails}
payload=(json.dumps(report,indent=2)+'\n').encode();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(__import__('gzip').compress(payload,mtime=0) if a.output.suffix=='.gz' else payload)
print(len(rows),fails)
for i in fails:print(i,rows[i]['case'],rows[i]['different_fields'],rows[i]['original']['error'],rows[i]['candidate']['error'])

if fails:raise SystemExit(1)
