#!/usr/bin/env python3
"""Offline original-vs-recovered Pump administrative instruction differential tests."""
import argparse, base64, hashlib, json, pathlib
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PROGRAM = Pubkey.from_string(IDL['address'])
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
AUTHORITY = Keypair.from_seed(bytes([201]) * 32)
PAYER = Keypair.from_seed(bytes([203]) * 32)
OUTSIDER = Keypair.from_seed(bytes([202]) * 32)
CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')
DATA = bytearray(base64.b64decode(CAPTURE['data_base64']))
DATA[9:41] = bytes(AUTHORITY.pubkey())


def execute(binary, instruction, arg, mutation):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, binary)
    vm.airdrop(PAYER.pubkey(), 10**12)
    vm.airdrop(AUTHORITY.pubkey(), 10**12)
    vm.airdrop(OUTSIDER.pubkey(), 10**12)
    data = bytearray(DATA)
    if mutation=='whitelist_empty':data[1013:1045]=bytes(32)
    if mutation=='whitelist_wsol':data[1013:1045]=bytes(Pubkey.from_string('So11111111111111111111111111111111111111112'))
    owner = PROGRAM
    global_key, event_key, program_key = GLOBAL, EVENT, PROGRAM
    authority = AUTHORITY
    signed = True
    global_write = authority_write = True
    if mutation == 'global_owner': owner = Pubkey.default()
    if mutation == 'global_discriminator': data[0] ^= 1
    if mutation == 'initialized_invalid': data[8] = 2
    if mutation.startswith('length_'): data = data[:int(mutation[7:])]
    if mutation == 'state_disabled':
        data[{'toggle_create_v2':450,'toggle_mayhem_mode':515,'toggle_cashback_enabled':740}[instruction]] = 0
    if mutation == 'global_truncated': data = data[:40]
    if mutation == 'global_address': global_key = Pubkey(bytes([91])*32)
    if mutation == 'global_readonly': global_write = False
    if mutation == 'authority_readonly': authority_write = False
    if mutation == 'authority_unsigned': signed = False
    if mutation == 'authority_wrong': authority = OUTSIDER
    if mutation == 'event_wrong': event_key = Pubkey(bytes([92])*32)
    if mutation == 'program_wrong': program_key = Pubkey.default()
    vm.set_account(global_key, Account(10**10, bytes(data), owner))
    metas = [AccountMeta(global_key, False, global_write), AccountMeta(authority.pubkey(), signed, authority_write), AccountMeta(event_key, False, False), AccountMeta(program_key, False, False)]
    if instruction=='update_global_authority':
        new_key=Pubkey.default() if mutation=='new_zero' else AUTHORITY.pubkey() if mutation=='new_same' else Pubkey(bytes([55])*32)
        metas.insert(2,AccountMeta(new_key,False,False))
    if instruction=='set_reserved_fee_recipients':
        count=int(mutation.split('_')[1]) if mutation.startswith('count_') else 8
        keys=[Pubkey(bytes([30+i])*32) for i in range(count)]
        if mutation=='recipient_duplicate':keys=[keys[0]]*count
        if mutation in ['recipient_zero','mixed_zero_low']:keys[-1]=Pubkey.default()
        if mutation=='recipient_program':keys[0]=PROGRAM
        for i,key in enumerate(keys):
            if key not in [Pubkey.default(),PROGRAM]:
                lamports=int(mutation.split('_')[1]) if mutation.startswith('rent_') and i==0 else 0 if mutation=='mixed_zero_low' and i==0 else 10**10
                vm.set_account(key,Account(lamports,bytes(64) if mutation=='recipient_data' else b'',PROGRAM if mutation=='recipient_owner' else Pubkey.default()))
        metas.extend(AccountMeta(key,False,False) for key in keys)
    if mutation == 'missing_event': metas = metas[:2]
    if mutation == 'missing_program': metas = metas[:3]
    discriminator = bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name'] == instruction))
    payload = arg if mutation == 'raw_instruction_data' else discriminator + arg
    ix = Instruction(PROGRAM, payload, metas)
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), [PAYER, authority] if signed else [PAYER], vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    result = {'error': str(r.err()) if failed else None,
              'data_hex': vm.get_account(global_key).data.hex(),
              'lamports': vm.get_account(global_key).lamports,
              'logs': meta.logs(),'event_payloads':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'payer_lamports':vm.get_account(PAYER.pubkey()).lamports,'authority_lamports':vm.get_account(authority.pubkey()).lamports}
    return result




p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--source-directory',type=pathlib.Path,default=ROOT/'programs/pump');p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate)
import gzip
original=ROOT/'evidence/original/pump/deployed.so';mutations=['none','global_owner','global_discriminator','global_truncated','global_address','global_readonly','authority_readonly','authority_unsigned','authority_wrong','event_wrong','program_wrong','missing_event','missing_program','initialized_invalid','length_1087','length_1088'];specs=[]
for name in ['update_global_authority','set_reserved_fee_recipients']:
 args=b'' if name=='update_global_authority' else bytes([55])*32
 specs.extend((name,args,m) for m in mutations)
 specs.extend((name,args,m) for m in (['new_zero','new_same'] if name=='update_global_authority' else ['count_'+str(n) for n in range(11)]+['recipient_duplicate','recipient_zero','recipient_owner','recipient_data','recipient_program','rent_0','rent_890879','rent_890880','mixed_zero_low']))
 specs.append((name,args+b'\xff','none'))
 if name=='set_reserved_fee_recipients':specs.extend((name,arg,'none') for arg in [b'',bytes(31),bytes(32)])
cases=[]
for name,args,mutation in specs:
 o=execute(original,name,args,mutation);n=execute(a.candidate,name,args,mutation);fields=['error','data_hex','lamports','payer_lamports','authority_lamports','event_payloads','inner_instructions'];different=[key for key in fields if o[key]!=n[key]];cases.append({'instruction':name,'args_hex':args.hex(),'mutation':mutation,'different_fields':different,'original':o,'candidate':n})
fails=[i for i,r in enumerate(cases) if r['different_fields']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources={str(p.relative_to(a.source_directory)):sha(p) for p in sorted(a.source_directory.rglob('*')) if p.is_file() and 'target' not in p.parts and (p.suffix=='.rs' or p.name in ['Cargo.toml','Cargo.lock'])}
report={'scope':'Two recovered authority/recipient administration handlers; all global state, errors, balances, raw events and CPI instructions compared in local synthetic fixtures.','candidate_sha256':sha(a.candidate),'original_sha256':sha(original),'source_sha256':sources,'case_count':len(cases),'mismatches':fails,'cases':cases};payload=(json.dumps(report,indent=2)+'\n').encode();a.output.write_bytes(gzip.compress(payload,mtime=0) if a.output.suffix=='.gz' else payload);print(len(cases),fails)
for i in fails:print(i,cases[i]['instruction'],cases[i]['mutation'],cases[i]['different_fields'],cases[i]['original']['error'],cases[i]['candidate']['error'])
if fails:raise SystemExit(1)
