#!/usr/bin/env python3
"""Validate partial SOL sell accounting against original SBF event and state effects."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, hashlib, json, struct, subprocess
import pump_trade_fixture as f
p=argparse.ArgumentParser();p.add_argument('--host',type=f.pathlib.Path,required=True);p.add_argument('--output',type=f.pathlib.Path,required=True);p.add_argument('--curve-report',type=f.pathlib.Path,default=f.R/'repro/pump/constant-product-differential.json',help='Report produced by pump_validate_constant_product.py');a=p.parse_args()
idl=json.loads((f.R/'evidence/upstream/pump.json').read_text());types={x['name']:x['type'] for x in idl['types']}
event_disc=bytes(next(x['discriminator'] for x in idl['events'] if x['name']=='TradeEvent'))
def decode_event(data):
    at=8
    def take(n):
        nonlocal at
        r=data[at:at+n];assert len(r)==n;at+=n;return r
    def read(t):
        if isinstance(t,str):
            if t=='pubkey':return str(f.Pubkey(take(32)))
            if t=='bool':return bool(take(1)[0])
            if t=='string':return take(int.from_bytes(take(4),'little')).decode()
            return int.from_bytes(take(int(t[1:])//8),'little',signed=t.startswith('i'))
        if 'defined' in t:
            return {x['name']:read(x['type']) for x in types[t['defined']['name']]['fields']}
        if 'vec' in t:return [read(t['vec']) for _ in range(int.from_bytes(take(4),'little'))]
        if 'array' in t:return [read(t['array'][0]) for _ in range(t['array'][1])]
        raise ValueError(t)
    result={x['name']:read(x['type']) for x in types['TradeEvent']['fields']}
    result['_unparsed_suffix_hex']=data[at:].hex()
    return result
initial={key:f.vm.get_account(key) for key in f.msg.account_keys}
user=f.Keypair.from_seed(bytes([231])*32);curve=f.Pubkey.from_string(f.x['accounts']['curve']);buyback=f.Pubkey.from_string(f.x['accounts']['buyback']);base=initial[curve]
curve_report_bytes=a.curve_report.read_bytes()
curve_report=json.loads(curve_report_bytes)
def require(value,message):
    if not value:raise ValueError('invalid constant-product report: '+message)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
require(curve_report.get('source_sha256')==sha(f.R/'programs/pump/recovered/constant_product.rs'),'arithmetic source differs')
require(curve_report.get('original_sha256')=={name:sha(f.R/'evidence/original'/name/'deployed.so') for name in ['pump','pump_fees']},'original ELF bindings differ')
require(curve_report.get('dependency_sha256')=={name:sha(f.R/'evidence/dependencies'/name/'deployed.so') for name in ['spl_token','spl_token_2022','associated_token']},'dependency ELF bindings differ')
source_cases=curve_report.get('cases')
require(isinstance(source_cases,list) and curve_report.get('case_count')==len(source_cases),'case count differs')
require(curve_report.get('mismatches')==[],'producer reported mismatches')
for case in source_cases:
    require(isinstance(case,dict) and type(case.get('compared')) is bool,'case comparison status missing')
    require(all(type(case.get(key)) is int and 0<=case[key]<2**64 for key in ['amount_in','reserve_in','reserve_out']),'case inputs are not u64 values')
    if case['compared']:
        require(case.get('match') is True and type(case.get('observed_quote_out')) is int and 0<=case['observed_quote_out']<2**64 and case.get('recovered_quote_out')==case['observed_quote_out'],'failed or incomplete arithmetic comparison')
    else:require(isinstance(case.get('error'),str) and bool(case['error']),'uncompared case has no original error')
compared=sum(case['compared'] for case in source_cases)
require(compared>=100 and curve_report.get('successful_comparisons')==compared,'successful comparison count differs')
source_cases=[dict(case) for case in source_cases]
rows=[];inputs=[]
actual_base,actual_quote=struct.unpack_from('<QQ',base.data,8)
for pb,cb in [(0,0),(95,0),(0,30),(100,100),(3000,3000),(10000,0),(0,10000),(6000,6000),(10001,0)]:
    for bb in [0,1,5000,9999,10000]:
        source_cases.append({'compared':True,'amount_in':10**9,'reserve_in':actual_base,'reserve_out':actual_quote,'observed_quote_out':(10**9*actual_quote)//(actual_base+10**9),'injected_fees':[pb,cb,bb]})
for case in source_cases:
    if not case['compared']:
        case=dict(case,compared=True,observed_quote_out=case['amount_in']*case['reserve_out']//(case['reserve_in']+case['amount_in']),injected_fees=[95,30,5000])
    for key,account in initial.items():
        if account is not None:f.vm.set_account(key,account)
    data=bytearray(base.data);struct.pack_into('<QQ',data,8,case['reserve_in'],case['reserve_out']);f.vm.set_account(curve,f.Account(base.lamports,bytes(data),base.owner))
    if 'injected_fees' in case:
        pb,cb,bb=case['injected_fees']
        fee_key=f.Pubkey.from_string(f.x['accounts']['fee_config']);fee_account=initial[fee_key]
        d=fee_account.data
        fees=struct.pack('<QQQ',0,pb,cb)
        encoded=d[:41]+fees+struct.pack('<I',1)+bytes(16)+fees+struct.pack('<I',0)+fees
        f.vm.set_account(fee_key,f.Account(fee_account.lamports,encoded.ljust(len(d),b'\0'),fee_account.owner))
        global_key=f.Pubkey.from_string(f.x['accounts']['global']);g=initial[global_key];gd=bytearray(g.data);struct.pack_into('<Q',gd,997,bb);f.vm.set_account(global_key,f.Account(g.lamports,bytes(gd),g.owner))
    ix=f.ixs[-1];trade=f.Instruction(ix.program_id,ix.data[:8]+struct.pack('<QQ',case['amount_in'],0),ix.accounts)
    r=f.vm.send_transaction(f.Transaction.new_signed_with_payer([*f.ixs[:-1],trade],user.pubkey(),[user],f.vm.latest_blockhash()))
    if isinstance(r,f.FailedTransactionMetadata):
        assert 'injected_fees' in case
        assert f.vm.get_account(curve).data==bytes(data)
        pb,cb,bb=case['injected_fees'];inputs.append(','.join(map(str,[case['observed_quote_out'],pb,cb,bb])))
        rows.append({'amount_in':case['amount_in'],'gross_quote_out':case['observed_quote_out'],'injected_fees':case['injected_fees'],'original_error':str(r.err()),'curve_rollback':True})
        continue
    events=[decode_event(raw) for line in r.logs() if line.startswith('Program data: ') and (raw:=f.base64.b64decode(line[14:])).startswith(event_disc)]
    assert len(events)==1;event=events[0];assert not event['is_buy']
    share=int.from_bytes(f.vm.get_account(f.Pubkey.from_string(f.x['accounts']['global'])).data[997:1005],'little')
    if 'injected_fees' in case:assert [event['fee_basis_points'],event['creator_fee_basis_points'],share]==case['injected_fees']
    inputs.append(','.join(map(str,[case['observed_quote_out'],event['fee_basis_points'],event['creator_fee_basis_points'],share])))
    after=f.vm.get_account(curve)
    row={'amount_in':case['amount_in'],'reserve_in':case['reserve_in'],'reserve_out':case['reserve_out'],'gross_quote_out':case['observed_quote_out'],'protocol_bps':event['fee_basis_points'],'creator_bps':event['creator_fee_basis_points'],'buyback_share_bps':share,'event_unparsed_suffix_hex':event['_unparsed_suffix_hex'],'original_event':{'protocol_fee':event['fee'],'creator_fee':event['creator_fee'],'buyback_fee':event['buyback_fee']},'original_effects':{'creator_accumulated':int.from_bytes(after.data[125:133],'little')-int.from_bytes(base.data[125:133],'little'),'protocol_accumulated':int.from_bytes(after.data[133:141],'little')-int.from_bytes(base.data[133:141],'little'),'user_output':f.vm.get_account(user.pubkey()).lamports-initial[user.pubkey()].lamports+5000,'buyback_output':f.vm.get_account(buyback).lamports-initial[buyback].lamports,'curve_lamports_spent':base.lamports-after.lamports}}
    row['injected_fees']=case.get('injected_fees')
    rows.append(row)
r=subprocess.run([str(a.host.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True);outputs=r.stdout.splitlines();assert len(outputs)==len(rows)
for row,out in zip(rows,outputs):
    if 'original_error' in row:
        row['recovered_error']=out
        row['match']=out.startswith('error:') and 'InstructionErrorCustom('+out.split(':')[1]+')' in row['original_error']
        continue
    protocol,creator,buyback_fee,user_out,retained=map(int,out.split(','));ev=row['original_event'];effects=row['original_effects']
    row['recovered']={'protocol_fee':protocol,'creator_fee':creator,'buyback_fee':buyback_fee,'user_output':user_out,'retained_protocol_fee':retained}
    row['match']=ev=={'protocol_fee':protocol,'creator_fee':creator,'buyback_fee':buyback_fee} and effects=={'creator_accumulated':creator,'protocol_accumulated':retained,'user_output':user_out,'buyback_output':buyback_fee,'curve_lamports_spent':user_out+buyback_fee}
failures=[i for i,row in enumerate(rows) if not row['match']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'Partial native SOL sell accounting versus original SBF. Protocol/creator rates are inputs observed from original events or explicitly injected fee schedules; this is not an independent reconstruction of fee selection. Captured external dependency fixture. No complete trade handler, byte identity, token-quote/reward/extension coverage claimed.','source_sha256':sha(f.R/'programs/pump/recovered/sell_accounting.rs'),'host_sha256':sha(a.host),'fixture_report_sha256':hashlib.sha256(curve_report_bytes).hexdigest(),'case_count':len(rows),'mismatches':failures,'cases':rows}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'case_count':len(rows),'mismatches':failures}));assert not failures
