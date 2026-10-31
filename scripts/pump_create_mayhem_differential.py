#!/usr/bin/env python3
"""End-to-end Mayhem-create differential.

Drives the real pump `create_v2` Mayhem-mode instruction, which internally
`invoke_signed`s into mayhem `initialize_mayhem_state` using pump's off-curve
["mint-authority"] PDA as the signer. A single valid transaction therefore
exercises BOTH pump's create_v2 Mayhem branch AND mayhem's initialize_mayhem_state
reached through the genuine pump->mayhem CPI (no synthetic signer, no oracle fake).

The oracle runs each case against the captured originals and, when a candidate pair
is supplied, against the independently rebuilt pump+mayhem binaries, then compares
account state, logs/events, inner instructions, return data and errors byte for byte.

Mayhem preconditions are built honestly: mayhem `global_params` is created by
sending mayhem's own `initialize_global_params`; the pump global is seeded from the
captured config snapshot with `create_v2_enabled`/`mayhem_mode_enabled` toggled.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, base64, gzip, hashlib, json, struct, sys
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport

ROOT = Path(__file__).resolve().parents[1]
IDL = json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PROGRAM = Pubkey.from_string(IDL['address'])
ORIGINAL_PUMP = ROOT/'evidence/original/pump/deployed.so'
ORIGINAL_MAYHEM = ROOT/'evidence/original/mayhem/deployed.so'
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
META = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
USER = Keypair.from_seed(bytes([211])*32)
MINT = Keypair.from_seed(bytes([212])*32)
ADMIN = Keypair.from_seed(bytes([214])*32)

GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
CURVE = Pubkey.find_program_address([b'bonding-curve', bytes(MINT.pubkey())], PROGRAM)[0]
MA = Pubkey.find_program_address([b'mint-authority'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
GLOBAL_PARAMS = Pubkey.find_program_address([b'global-params'], MAYHEM)[0]
SOL_VAULT = Pubkey.find_program_address([b'sol-vault'], MAYHEM)[0]
MAYHEM_STATE = Pubkey.find_program_address([b'mayhem-state', bytes(MINT.pubkey())], MAYHEM)[0]

def _ata(owner, mint, prog=TOKEN22):
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(mint)], ATA)[0]
ABC = _ata(CURVE, MINT.pubkey())
MTV = _ata(SOL_VAULT, MINT.pubkey())

CAPTURE = next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump')

NAMES = {'mint':MINT.pubkey(),'mint_authority':MA,'bonding_curve':CURVE,'associated_bonding_curve':ABC,
         'global':GLOBAL,'user':USER.pubkey(),'system_program':Pubkey.default(),'token_program':TOKEN22,
         'associated_token_program':ATA,'mayhem_program_id':MAYHEM,'global_params':GLOBAL_PARAMS,
         'sol_vault':SOL_VAULT,'mayhem_state':MAYHEM_STATE,'mayhem_token_vault':MTV,
         'event_authority':EVENT,'program':PROGRAM}
# Accounts whose bytes are compared; programs are skipped automatically.
SNAP_KEYS = sorted({str(v) for v in NAMES.values()})

def _string(s):
    b=s.encode(); return struct.pack('<I',len(b))+b

def _anchor_disc(name):
    return hashlib.sha256(b'global:'+name.encode()).digest()[:8]

def _init_global_params(vm):
    metas=[AccountMeta(ADMIN.pubkey(),True,True),AccountMeta(GLOBAL_PARAMS,False,True),AccountMeta(Pubkey.default(),False,False)]
    tx=Transaction.new_signed_with_payer([Instruction(MAYHEM,_anchor_disc('initialize_global_params'),metas)],ADMIN.pubkey(),[ADMIN],vm.latest_blockhash())
    return vm.send_transaction(tx)

def run(c, pump_bin=ORIGINAL_PUMP, mayhem_bin=ORIGINAL_MAYHEM):
    pump_bin = pin_program(pump_bin)
    mayhem_bin = pin_program(mayhem_bin)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, pump_bin)
    vm.add_program_from_file(MAYHEM, mayhem_bin)
    for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA),('token_metadata',META)]:
        vm.add_program_from_file(key, ROOT/'evidence/dependencies'/name/'deployed.so')
    vm.set_clock(Clock(100,1700000000,0,0,1700000000))
    vm.airdrop(USER.pubkey(), 10**12)
    vm.airdrop(ADMIN.pubkey(), 10**12)
    # pump global from capture, with create_v2 + mayhem toggles per case.
    gd = bytearray(base64.b64decode(CAPTURE['data_base64']))
    gd[450] = c.get('create_v2_enabled', 1)
    gd[515] = c.get('mayhem_mode_enabled', 1)
    for off,hexdata in c.get('global_patches',[]):
        gd[off:off+len(bytes.fromhex(hexdata))] = bytes.fromhex(hexdata)
    vm.set_account(GLOBAL, Account(10**9, bytes(gd), PROGRAM))
    # mayhem global_params via its own initializer, unless the case opts out.
    if c.get('init_global_params', True):
        r = _init_global_params(vm)
        if isinstance(r, FailedTransactionMetadata):
            raise SystemExit('setup: initialize_global_params failed: %s' % r.err())
        # Optional genuine-state patch of the duration byte (global_params.reset_middle[0]@137).
        dur = c.get('duration_hours')
        if dur is not None:
            a = vm.get_account(GLOBAL_PARAMS); d = bytearray(a.data); d[137] = dur
            vm.set_account(GLOBAL_PARAMS, Account(a.lamports, bytes(d), a.owner))
    ix = next(x for x in IDL['instructions'] if x['name']=='create_v2')
    metas = [AccountMeta(NAMES[a['name']], a.get('signer',False), a.get('writable',False)) for a in ix['accounts']]
    if c.get('wrong'):
        metas = [AccountMeta(OTHER.pubkey() if m.pubkey==NAMES[c['wrong']] else m.pubkey, m.is_signer, m.is_writable) for m in metas]
    payload = (bytes(ix['discriminator']) + _string(c.get('name','Synthetic Coin')) + _string(c.get('symbol','SYNTH'))
               + _string(c.get('uri','https://example.invalid/metadata.json')) + bytes(Pubkey.from_string(c.get('creator', str(USER.pubkey()))))
               + bytes([1 if c.get('is_mayhem_mode',True) else 0]) + bytes.fromhex(c.get('optional_args','')))
    signers = [k for k in [USER,MINT] if k.pubkey() in {m.pubkey for m in metas if m.is_signer}|{USER.pubkey()}]
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1400000), Instruction(PROGRAM,payload,metas)], USER.pubkey(), signers, vm.latest_blockhash())
    assert all(tx.verify_with_results())
    def snap():
        out={}
        for k in SNAP_KEYS:
            key=Pubkey.from_string(k); a=vm.get_account(key)
            if a and a.executable: continue
            out[k]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
        return out
    before=snap()
    r=vm.send_transaction(tx)
    fail=isinstance(r,FailedTransactionMetadata); m=r.meta() if fail else r; raw=json.loads(m.to_json())
    return {'before':before,'after':snap(),'error':str(r.err()) if fail else None,
            'logs':m.logs(),'events':[l for l in m.logs() if l.startswith('Program data:')],
            'inner':raw['inner_instructions'],'return':raw.get('return_data')}

def cases():
    out=[{'case':'mayhem-base'}]
    out += [{'case':'duration-%d'%d,'duration_hours':d} for d in [0,1,7,24,255]]
    out += [{'case':'mayhem-disabled','mayhem_mode_enabled':0},
            {'case':'create-v2-disabled','create_v2_enabled':0},
            {'case':'global-params-uninitialized','init_global_params':False},
            {'case':'normal-mode-regression','is_mayhem_mode':False}]
    for field,n in [('name',32),('name',33),('symbol',13),('symbol',14),('uri',200),('uri',201)]:
        out.append({'case':'%s-%d'%(field,n),field:'x'*n})
    out += [{'case':'zero-creator-is-rejected','creator':str(Pubkey.default()),'is_mayhem_mode':True}]
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate-pump',type=Path)
    p.add_argument('--candidate-mayhem',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if bool(a.candidate_pump) != bool(a.candidate_mayhem):
        p.error('--candidate-pump and --candidate-mayhem must be supplied together')
    publisher=PumpReport(a.output,ROOT,a.candidate_pump,__file__,extra_inputs=[ROOT/'evidence/original/mayhem/deployed.so',*([a.candidate_mayhem] if a.candidate_mayhem else [])])
    if a.candidate_pump:
        a.candidate_pump = pin_program(a.candidate_pump)
        a.candidate_mayhem = pin_program(a.candidate_mayhem)
    has_cand = bool(a.candidate_pump)
    rows=[]; bad=[]
    for c in cases():
        x=run(c)
        y=run(c,a.candidate_pump,a.candidate_mayhem) if has_cand else None
        diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]]
        rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
        if diff: bad.append(c['case'])
    report={'scope':'End-to-end pump create_v2 Mayhem-mode -> mayhem initialize_mayhem_state via the real pump->mayhem invoke_signed CPI. No byte-identity claim.',
            'original_pump_sha256':hashlib.sha256(pin_program(ORIGINAL_PUMP).read_bytes()).hexdigest(),
            'original_mayhem_sha256':hashlib.sha256(pin_program(ORIGINAL_MAYHEM).read_bytes()).hexdigest(),
            'candidate_pump_sha256':hashlib.sha256(a.candidate_pump.read_bytes()).hexdigest() if has_cand else None,
            'candidate_mayhem_sha256':hashlib.sha256(a.candidate_mayhem.read_bytes()).hexdigest() if has_cand else None,
            'cases':rows,'mismatches':bad,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    publisher.write(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0))
    print(len(rows),'cases',len(bad),'mismatches')
    if bad: print('MISMATCHES:', bad); raise SystemExit(1)

OTHER = Keypair.from_seed(bytes([213])*32)
if __name__=='__main__':
    main()
