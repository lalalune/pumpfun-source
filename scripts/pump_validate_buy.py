#!/usr/bin/env python3
"""Compare the partial regular-SOL buy-v3 SBF path with the captured original."""
import argparse, hashlib, json, struct
import pump_trade_fixture as f
from pump_amm_reusable_harness import pin_program
p=argparse.ArgumentParser();p.add_argument('--candidate',type=f.pathlib.Path,required=True);p.add_argument('--source-directory',type=f.pathlib.Path,default=f.R/'programs/pump');p.add_argument('--output',type=f.pathlib.Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate)
program=f.Pubkey.from_string(f.x['program']);user=f.Keypair.from_seed(bytes([231])*32)
initial={key:f.vm.get_account(key) for key in f.msg.account_keys}
curve=f.Pubkey.from_string(f.x['accounts']['curve']);global_key=f.Pubkey.from_string(f.x['accounts']['global']);fee_key=f.Pubkey.from_string(f.x['accounts']['fee_config'])
math=json.loads((f.R/'repro/pump/constant-product-differential.json').read_text())['cases']
base_in,base_out=struct.unpack_from('<QQ',initial[curve].data,8)
cases=[{'amount':c['amount_in'],'max_cost':0,'reserve_in':c['reserve_in'],'reserve_out':c['reserve_out']} for c in math]
for amount,minimum,mutation in [(0,0,'none'),(500000000,10**12,'none'),(10**9+1,0,'none'),(500000000,0,'complete'),(500000000,0,'creator_zero'),(500000000,0,'wrong_buyback'),(500000000,0,'empty_tiers'),(500000000,0,'global_discriminator'),(500000000,0,'fee_owner'),(500000000,0,'curve_readonly'),(500000000,0,'base_user_wrong_owner')]:
    cases.append({'amount':amount,'max_cost':minimum,'reserve_in':base_in,'reserve_out':base_out,'mutation':mutation})
for pb,cb in [(0,0),(95,0),(0,30),(100,100),(3000,3000),(10000,0),(0,10000),(6000,6000),(10001,0)]:
    for bb in [0,1,5000,9999,10000]:cases.append({'amount':10**9,'max_cost':0,'reserve_in':base_in,'reserve_out':base_out,'fees':[pb,cb,bb]})

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
    trade=f.Instruction(ix.program_id,bytes.fromhex('07051dc4f5176550')+struct.pack('<QQ',c['amount'],c['max_cost'])+bytes(c.get('trailing',[])),metas)
    result=vm.send_transaction(f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],user.pubkey(),[user],vm.latest_blockhash()))
    failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta() if failed else result
    state={}
    for key in set(f.msg.account_keys)|set(m.pubkey for m in metas):
        if key==program:continue # Executable image is deliberately different; compared separately by whole-file build receipt.
        account=vm.get_account(key)
        if account:state[str(key)]={'lamports':account.lamports,'data_sha256':hashlib.sha256(account.data).hexdigest(),'owner':str(account.owner)}
    return {'error':str(result.err()) if failed else None,'accounts':state,'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'event_payloads':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'logs':meta.logs()}
cases=[dict(c,max_cost=10**12) for c in cases]
cases.append({'amount':500000000,'max_cost':1,'reserve_in':base_in,'reserve_out':base_out})
cases.extend({'amount':v,'max_cost':10**12,'reserve_in':base_in,'reserve_out':base_out,'real_base':500000000} for v in [499999999,500000000,500000001,1000000000])
cases.extend({'amount':1000000000,'max_cost':maximum,'reserve_in':base_in,'reserve_out':base_out,'trailing':trailing} for maximum in [0,1,100,10000,28309,28310,10**12] for trailing in [[],[0],[1],[2]])

base={'amount':500000000,'max_cost':1000000000000,'reserve_in':base_in,'reserve_out':base_out}
cases.extend(dict(base,fee_len=n) for n in [0,1,7,8,100,2511,2512,3000,4072,4073,4096,4097,5000])
cases.append(dict(base,fee_disc=True))
for flags in [[],[81],[124],[81,124],[82],[81,82],[82,124]]:
 for fees in [[95,30,5000],[1,1,1],[0,30,10000],[3000,3000,9999]]:
  for amount in [35767,500000000]:cases.append(dict(base,amount=amount,flags=flags,fees=fees,distinct_flat=True))
 for mutation in ['creator_zero','wrong_buyback']:cases.append(dict(base,flags=flags,mutation=mutation))

rows=[]
for c in cases:
    original=run(f.R/'evidence/original/pump/deployed.so',c);candidate=run(a.candidate,c)
    keys=['error','accounts','event_payloads','inner_instructions'];diff=[k for k in keys if original[k]!=candidate[k]]
    rows.append({'case':c,'match':not diff,'different_fields':diff,'original':original,'candidate':candidate})
failures=[i for i,r in enumerate(rows) if not r['match']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={str(path.relative_to(a.source_directory)):sha(path) for path in sorted(a.source_directory.rglob('*')) if path.is_file() and 'target' not in path.parts and (path.suffix=='.rs' or path.name in ['Cargo.toml','Cargo.lock'])}
report={'scope':'Partial SOL including Mayhem/holder-reward accounting and cashback rejection buy_v3 path, not a complete instruction reconstruction. Compares errors, all instruction-account bytes/owners/lamports except the replaced executable Pump image, raw event payloads and full recorded inner instructions. Captured external token dependencies loaded explicitly; no public RPC.','source_sha256':sources,'original_sha256':sha(f.R/'evidence/original/pump/deployed.so'),'candidate_sha256':sha(a.candidate),'case_count':len(rows),'mismatches':failures,'cases':rows}
a.output.parent.mkdir(parents=True,exist_ok=True);payload=(json.dumps(report,indent=2)+'\n').encode();a.output.write_bytes(__import__('gzip').compress(payload,mtime=0) if a.output.suffix=='.gz' else payload);print(json.dumps({'case_count':len(rows),'mismatches':failures}))
for i in failures:
    r=rows[i];print(i,r['case'],r['different_fields'],r['original']['error'],r['candidate']['error'])
if failures:raise SystemExit(1)
