#!/usr/bin/env python3
"""Authorized sequential burns; genuine input bytes, ordinary signatures, no reset."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path
import argparse, base64, hashlib, importlib.metadata, json, re, struct
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.account import Account
from solders.clock import Clock
from solders.keypair import Keypair
from solders.instruction import AccountMeta, Instruction
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.compute_budget import set_compute_unit_limit
import solders.solders

REPO=Path(__file__).resolve().parents[1];ROOT=None
MAY=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
TOKEN=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
CLOCK=Pubkey.from_string('SysvarC1ock11111111111111111111111111111111')
FIELDS=['mayhem_state','mint','mayhem_token_vault','sol_vault','bonding_curve','global',
        'pump_program','pump_event_authority','system_program','token_program','event_authority','program']
sha=lambda b:hashlib.sha256(b).hexdigest()
PAYER=Keypair.from_seed(hashlib.sha256(b'mayhem-burn-genuine-fixture-ordinary-test-payer-v1').digest())

def snapshot(vm,keys):
    out={}
    for key in keys:
        a=vm.get_account(Pubkey.from_string(key))
        out[key]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'executable':a.executable,
            'rent_epoch':a.rent_epoch,'data_bytes':len(a.data),'data_sha256':sha(a.data),
            'data_base64':base64.b64encode(a.data).decode() if not a.executable else None}
    return out

def norm_logs(logs):
    return [re.sub(r' consumed \d+ of \d+ compute units',' consumed <units> of <budget> compute units',line) for line in logs]

def run(binary,family,manifest,index,side,outdir):
    captured=manifest['snapshots']['eligible']['accounts'];fields=family['accounts']
    vm=LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
    for program,path in [(MAY,binary),(PUMP,REPO/'evidence/original/pump/deployed.so'),
                         (TOKEN,REPO/'evidence/dependencies/spl_token_2022/deployed.so')]:
        vm.add_program_from_file(program,path)
    # Standard VM executable loading is explicit. Business accounts below retain
    # every captured byte and metadata field. Absent accounts remain absent.
    load_checks={}
    keys=list(dict.fromkeys(list(fields.values())+[str(CLOCK),str(PAYER.pubkey())]))
    for key in keys:
        if key==str(PAYER.pubkey()):continue
        row=captured[key]
        if not row['exists']:
            assert vm.get_account(Pubkey.from_string(key)) is None
            load_checks[key]={'captured_absence_preserved':True};continue
        if row['executable']:
            assert vm.get_account(Pubkey.from_string(key)).executable
            load_checks[key]={'runtime_program_loader':True,'captured_account_owner':row['owner']};continue
        data=(ROOT/row['data_file']).read_bytes();assert sha(data)==row['data_sha256']
        vm.set_account(Pubkey.from_string(key),Account(row['lamports'],data,Pubkey.from_string(row['owner']),False,row['rentEpoch']))
        load_checks[key]={'captured_sha256':sha(data),'exact_nonexecutable_metadata_and_bytes':True}
    raw_clock=(ROOT/captured[str(CLOCK)]['data_file']).read_bytes()
    c=Clock(*struct.unpack('<QqQQq',raw_clock));vm.set_clock(c)
    # set_clock changes the sysvar cache; retain captured account metadata too.
    cr=captured[str(CLOCK)]
    vm.set_account(CLOCK,Account(cr['lamports'],raw_clock,Pubkey.from_string(cr['owner']),False,cr['rentEpoch']))
    assert vm.get_clock()==c and vm.get_account(CLOCK).data==raw_clock
    # Explicitly authorized ordinary test-owned funded payer; never a PDA.
    assert PAYER.pubkey().is_on_curve() and str(PAYER.pubkey()) not in captured
    vm.set_account(PAYER.pubkey(),Account(10_000_000_000,b'',Pubkey.default()))
    before=snapshot(vm,keys)
    for key,row in captured.items():
        if key not in before or not row['exists'] or row['executable']:continue
        observed=before[key]
        assert observed['data_sha256']==row['data_sha256'] and observed['lamports']==row['lamports']
        assert observed['owner']==row['owner'] and observed['rent_epoch']==row['rentEpoch']
    event=fields['event_authority'];assert before[event] is None
    metas=[AccountMeta(Pubkey.from_string(fields[k]),False,i<5) for i,k in enumerate(FIELDS)]
    tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1_000_000),
        Instruction(MAY,hashlib.sha256(b'global:burn_tokens').digest()[:8],metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash())
    assert tx.verify_with_results()==[True]
    raw=bytes(tx);(outdir/f'{index}-{side}.transaction.bin').write_bytes(raw)
    result=vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata)
    metadata=result.meta() if failed else result;meta=json.loads(metadata.to_json());after=snapshot(vm,keys)
    assert bytes(tx)==raw and tx.verify_with_results()==[True]
    for key in [str(MAY),str(PUMP),str(TOKEN),str(Pubkey.default())]:assert before[key]==after[key]
    # Continue in the same VM from the successful post-state without any
    # account writes. A new runtime blockhash prevents duplicate-message reuse.
    assert not failed
    previous_blockhash=vm.latest_blockhash();vm.expire_blockhash()
    assert vm.latest_blockhash()!=previous_blockhash
    second=Transaction.new_signed_with_payer([set_compute_unit_limit(1_000_000),
        Instruction(MAY,hashlib.sha256(b'global:burn_tokens').digest()[:8],metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash())
    assert second.verify_with_results()==[True] and bytes(second)!=raw
    second_raw=bytes(second);(outdir/f'{index}-{side}.second.transaction.bin').write_bytes(second_raw)
    second_result=vm.send_transaction(second)
    assert isinstance(second_result,FailedTransactionMetadata)
    second_meta=json.loads(second_result.meta().to_json())
    second_after=snapshot(vm,keys)
    sequential={'transaction_sha256':sha(second_raw),'transaction_base64':base64.b64encode(second_raw).decode(),
        'signature':str(second.signatures[0]),'signature_valid':second.verify_with_results()==[True],
        'new_blockhash':str(second.message.recent_blockhash),'first_blockhash':str(tx.message.recent_blockhash),
        'before':after,'after':second_after,'error':str(second_result.err()),'metadata':second_meta,
        'logs_without_compute_numbers':norm_logs(second_meta['logs'])}
    assert 'Custom(6004)' in sequential['error']
    for key in after:
        expected=after[key]
        if key==str(PAYER.pubkey()):expected=dict(expected,lamports=expected['lamports']-5000)
        assert second_after[key]==expected
    state=vm.get_account(Pubkey.from_string(fields['mayhem_state']));mint=vm.get_account(Pubkey.from_string(fields['mint']));vault=vm.get_account(Pubkey.from_string(fields['mayhem_token_vault']))
    parsed={'status':state.data[97],'burned_amount':struct.unpack_from('<Q',state.data,98)[0],
            'mint_supply':struct.unpack_from('<Q',mint.data,36)[0],'vault_amount':struct.unpack_from('<Q',vault.data,64)[0]}
    logs=metadata.logs();events=[z for z in logs if z.startswith('Program data: ')]
    return {'sequential_second':sequential,'binary_sha256':sha(binary.read_bytes()),'signature':str(tx.signatures[0]),'transaction_sha256':sha(raw),
       'transaction_base64':base64.b64encode(raw).decode(),'ordinary_payer':str(PAYER.pubkey()),
       'signature_verified_before_and_after':True,'runtime_sigverify':True,'runtime_blockhash_check':True,
       'captured_clock':family['clock'],'fixture_load_checks':load_checks,'before':before,'after':after,
       'error':str(result.err()) if failed else None,'parsed_after':parsed,'logs':logs,
       'logs_without_compute_numbers':norm_logs(logs),'events':events,'inner_instructions':meta['inner_instructions'],
       'return_data':meta['return_data'],'compute_units_consumed':metadata.compute_units_consumed(),
       'metadata':meta,'event_authority_absent_before':before[event] is None,'event_authority_absent_after':after[event] is None}

def main():
    global ROOT
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);a=p.parse_args();ROOT=a.fixtures.resolve()
    manifest_path=ROOT/'fixture-manifest.json';manifest=json.loads(manifest_path.read_text())
    # A manifest that selects no family would publish an empty comparison that
    # looks like a clean run; refuse before creating any output.
    if not manifest['eligible_families']:raise SystemExit('fixture manifest selects no eligible families: '+str(manifest_path))
    a.output.mkdir(parents=True,exist_ok=False)
    original=REPO/'evidence/original/mayhem/deployed.so'
    candidate=a.candidate.resolve()
    inputs={'fixtures:fixture-manifest.json':sha(manifest_path.read_bytes()),
            str(original.relative_to(REPO)):sha(original.read_bytes()),str(candidate.relative_to(REPO)):sha(candidate.read_bytes())}
    for row in manifest['snapshots']['eligible']['accounts'].values():
        if row['exists']:inputs['fixtures:'+row['data_file']]=sha((ROOT/row['data_file']).read_bytes())
    cases=[]
    for i,family in enumerate(manifest['eligible_families']):
        x=run(original,family,manifest,i,'original',a.output)
        y=run(candidate,family,manifest,i,'candidate',a.output)
        differences=[]
        for k in ['error','parsed_after','events','inner_instructions','return_data','logs_without_compute_numbers']:
            if x[k]!=y[k]:differences.append(k)
        for phase in ['before','after']:
            # The only program varying between runs is the compiled subject;
            # its exact loader account and hash stay in both raw receipts.
            xx={k:v for k,v in x[phase].items() if k!=str(MAY)}
            yy={k:v for k,v in y[phase].items() if k!=str(MAY)}
            if xx!=yy:differences.append(phase)
        for k in ['error','logs_without_compute_numbers','transaction_base64']:
            if x['sequential_second'][k]!=y['sequential_second'][k]:differences.append('second.'+k)
        for phase in ['before','after']:
            if {k:v for k,v in x['sequential_second'][phase].items() if k!=str(MAY)}!={k:v for k,v in y['sequential_second'][phase].items() if k!=str(MAY)}:differences.append('second.'+phase)
        if x['sequential_second']['metadata']['inner_instructions']!=y['sequential_second']['metadata']['inner_instructions']:differences.append('second.inner_instructions')
        same_message=x['transaction_base64']==y['transaction_base64']
        if not same_message:differences.append('signed_message')
        cases.append({'index':i,'mint':family['accounts']['mint'],'original':x,'candidate':y,
                      'same_signed_message':same_message,'different_fields':differences})
        (a.output/f'case-{i}.json').write_text(json.dumps(cases[-1],indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'case':i,'original_error':x['error'],'candidate_error':y['error'],'different_fields':differences}),flush=True)
    assert inputs=={path:sha(((ROOT/path.removeprefix('fixtures:')) if path.startswith('fixtures:') else (REPO/path)).read_bytes()) for path in inputs}
    out={'scope':'Three two-step offline burn sequences over exact public eligible snapshots, not historical replay. Each second transaction uses the first transaction post-state without writes/resets and a new blockhash. Signature and blockhash checks enabled. Only the explicitly authorized ordinary test payer is funded. No initializer or privileged state edits.',
         'input_sha256':inputs,'solders_version':importlib.metadata.version('solders'),
         'solders_binary_sha256':sha(Path(solders.solders.__file__).read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),
         'program_loading':'LiteSVM add_program_from_file loads exact unchanged executable bytes under the local legacy loader. These loader account owner/rent metadata differ from mainnet upgradeable program accounts and are retained in receipts. All captured nonexecutable accounts and Clock retain exact captured metadata/bytes.',
         'case_count':len(cases),'signed_transactions':len(cases)*4,'inputs_unchanged':True,
         'mismatches':[c['index'] for c in cases if c['different_fields']],
         'raw_log_equality':[c['original']['logs']==c['candidate']['logs'] for c in cases],
         'log_comparison':'Retain raw logs. Compare additionally after replacing only consumed/remaining compute-unit numbers; never remove error or instruction lines.',
         'cases':cases}
    (a.output/'comparison.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'case_count':len(cases),'mismatches':out['mismatches'],'inputs_unchanged':True}))
    raise SystemExit(bool(out['mismatches']))

if __name__=='__main__':main()
