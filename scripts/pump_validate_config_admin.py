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
import struct,gzip
original=ROOT/'evidence/original/pump/deployed.so';u=lambda n:struct.pack('<Q',n)
arguments={
'add_quote_mint':[bytes(Pubkey.from_string(key)) for key in ['11111111111111111111111111111111','So11111111111111111111111111111111111111112','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v']]+[bytes([55])*32],
'remove_quote_mint':[bytes(Pubkey.from_string(key)) for key in ['11111111111111111111111111111111','So11111111111111111111111111111111111111112','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v']]+[bytes([55])*32],
'set_virtual_quote_reserves':[u(n) for n in [0,1,10000,2**64-1]],
'update_buyback_config':[b'\0']+[b'\1'+u(n) for n in [0,1,9999,10000,10001,2**64-1]]+[b'\2',b'\1'],
'update_creator_fee_config':[bytes([flag])+u(n) for flag in [0,1,2] for n in [0,1,10000,10001,2**64-1]],
'update_holder_reward_config':[bytes([flag])+key for flag in [0,1,2] for key in [bytes(32),bytes([55])*32,bytes([255])*32]]}
mutations=['none','global_owner','global_discriminator','global_truncated','global_address','global_readonly','authority_readonly','authority_unsigned','authority_wrong','event_wrong','program_wrong','missing_event','missing_program','initialized_invalid','length_1087','length_1088']
cases=[]
for name,args_list in arguments.items():
 for args in args_list+[b'',args_list[0]+b'\xff']:
  for mutation in ((mutations if args in args_list[:3] else ['none'])+(['whitelist_empty','whitelist_wsol'] if 'quote_mint' in name else [])):
   o=execute(original,name,args,mutation);n=execute(a.candidate,name,args,mutation);fields=['error','data_hex','lamports','payer_lamports','authority_lamports','event_payloads','inner_instructions'];different=[key for key in fields if o[key]!=n[key]];cases.append({'instruction':name,'args_hex':args.hex(),'mutation':mutation,'different_fields':different,'original':o,'candidate':n})
fails=[i for i,r in enumerate(cases) if r['different_fields']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources={str(p.relative_to(a.source_directory)):sha(p) for p in sorted(a.source_directory.rglob('*')) if p.is_file() and 'target' not in p.parts and (p.suffix=='.rs' or p.name in ['Cargo.toml','Cargo.lock'])}
report={'scope':'Six additional recovered configuration administration handlers. Compares errors, global bytes and lamports, signer/payer balances, raw events and complete inner CPI instructions. Local synthetic authority, no network transactions.','candidate_sha256':sha(a.candidate),'original_sha256':sha(original),'source_sha256':sources,'case_count':len(cases),'mismatches':fails,'cases':cases};payload=(json.dumps(report,indent=2)+'\n').encode();a.output.write_bytes(gzip.compress(payload,mtime=0) if a.output.suffix=='.gz' else payload);print(len(cases),fails)
for i in fails:print(i,cases[i]['instruction'],cases[i]['mutation'],cases[i]['different_fields'],cases[i]['original']['error'],cases[i]['candidate']['error'])
if fails:raise SystemExit(1)
