#!/usr/bin/env python3
"""Differential oracle for pump `set_mayhem_virtual_params` (dormant, CPI-only).

`set_mayhem_virtual_params` requires account #0 `sol_vault_authority` (mayhem's
["sol-vault"] PDA) to sign, so it is reachable only through a mayhem `invoke_signed`
CPI. No program in the captured system (original pump or original mayhem) calls it, so
there is no genuine caller to replay. This oracle therefore drives it through a minimal
signer-forwarder stub deployed at the mayhem program id, which signs the ["sol-vault"]
PDA honestly via `invoke_signed` (a real signature, not a LiteSVM signer bypass) and
forwards the 8 handler accounts to pump. The identical, genuinely-authorized transaction
is run against both the captured original pump and a candidate pump; account state,
errors, logs and the emitted event are compared byte-for-byte. Semantic recovery only;
no whole-binary byte-identity claim.

The formula (reverse-engineered empirically from the original and confirmed here):
  if is_mayhem_mode:
    den = 2*token_total_supply - global.initial_real_token_reserves - mayhem_token_vault.amount   # underflow -> Overflow(6024)
    if real_quote_reserves >= 10_000_000:
      raw = real_quote_reserves + (real_quote_reserves * virtual_token_reserves) // den            # u128
      cap = 2_000_000_000_000 if quote_mint == default else 160_000_000_000
      virtual_quote_reserves = min(raw, cap)
  emit UpdateMayhemVirtualParamsEvent{...}   # always
"""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import argparse, base64, hashlib, json, struct
from pump_differential_output import PumpReport
from pathlib import Path
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program

ROOT = Path(__file__).resolve().parents[1]
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
STUB = ROOT / 'scripts/fixtures/signer_stub.so'
DEPENDENCIES = {TOKEN22: ROOT / 'evidence/dependencies/spl_token_2022/deployed.so',
                ATA: ROOT / 'evidence/dependencies/associated_token/deployed.so'}
BC_DISC = bytes([23, 183, 248, 55, 96, 216, 172, 96])
SMVP_DISC = bytes([61, 169, 188, 191, 153, 149, 42, 97])
CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')
IRTR_OFF = 8 + 1 + 32 + 32 + 8 + 8   # global.initial_real_token_reserves
PAYER = Keypair.from_seed(bytes([240]) * 32)
MINT = Keypair.from_seed(bytes([241]) * 32).pubkey()
SOL_VAULT = Pubkey.find_program_address([b'sol-vault'], MAYHEM)
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
CURVE = Pubkey.find_program_address([b'bonding-curve', bytes(MINT)], PUMP)[0]
EVENT_AUTH = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
MTV = Pubkey.find_program_address([bytes(SOL_VAULT[0]), bytes(TOKEN22), bytes(MINT)], ATA)[0]
QM_SPL = Pubkey.from_string('So11111111111111111111111111111111111111112')
sha = lambda b: hashlib.sha256(b).hexdigest()


def bc_data(vtr, vqr, rtr, rqr, tts, quote_mint, is_mayhem):
    d = bytearray(BC_DISC)
    d += struct.pack('<QQQQQ', vtr, vqr, rtr, rqr, tts)
    d += bytes([0]) + bytes(Pubkey.default()) + bytes([1 if is_mayhem else 0, 0]) + bytes(quote_mint)
    d += struct.pack('<Q', 0) + bytes([0, 0]) + struct.pack('<QQ', 0, 0) + bytes([0]) + struct.pack('<QQQ', 0, 0, 0)
    assert len(d) == 166
    return bytes(d)


def tok(mint, owner, amount):
    d = bytearray(165); d[0:32] = bytes(mint); d[32:64] = bytes(owner); d[64:72] = struct.pack('<Q', amount); d[108] = 1
    return bytes(d)


def mint_acct():
    d = bytearray(82); d[36:44] = struct.pack('<Q', 0); d[44] = 6; d[45] = 1
    return bytes(d)


def run(pump_bin, c):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PUMP, str(pump_bin))
    vm.add_program_from_file(MAYHEM, str(pin_program(STUB)))
    for program, path in DEPENDENCIES.items():
        vm.add_program_from_file(program, str(pin_program(path)))
    vm.airdrop(PAYER.pubkey(), 10**10)
    g = bytearray(base64.b64decode(CAPTURE['data_base64']))
    g[IRTR_OFF:IRTR_OFF + 8] = struct.pack('<Q', c['irtr'])
    vm.set_account(GLOBAL, Account(10**9, bytes(g), PUMP))
    vm.set_account(MINT, Account(10**9, mint_acct(), TOKEN22))
    vm.set_account(MTV, Account(10**9, tok(MINT, SOL_VAULT[0], c['vault']), TOKEN22))
    qm = QM_SPL if c['spl'] else Pubkey.default()
    vm.set_account(CURVE, Account(10**9, bc_data(c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['tts'], qm, c['mayhem']), PUMP))
    vm.set_account(SOL_VAULT[0], Account(10**9, b'', MAYHEM))
    data = struct.pack('<H', len(SMVP_DISC)) + SMVP_DISC + bytes([2, 9]) + b'sol-vault' + bytes([1, SOL_VAULT[1]])
    metas = [AccountMeta(PUMP, False, False), AccountMeta(SOL_VAULT[0], False, True), AccountMeta(MTV, False, True),
             AccountMeta(MINT, False, False), AccountMeta(GLOBAL, False, False), AccountMeta(CURVE, False, True),
             AccountMeta(TOKEN22, False, False), AccountMeta(EVENT_AUTH, False, False), AccountMeta(PUMP, False, False)]
    tx = Transaction.new_signed_with_payer([Instruction(MAYHEM, data, metas)], PAYER.pubkey(), [PAYER], vm.latest_blockhash())
    res = vm.send_transaction(tx)
    failed = isinstance(res, FailedTransactionMetadata)
    logs = list(res.meta().logs()) if failed else list(res.logs())
    out = {'err': str(res.err()) if failed else None,
           'events': sorted(l.removeprefix('Program data: ') for l in logs if l.startswith('Program data: ')),
           'logs': [l for l in logs if 'Instruction:' in l or 'AnchorError' in l or 'failed' in l]}
    if not failed:
        bc = vm.get_account(CURVE).data
        out['vqr'] = struct.unpack('<Q', bc[16:24])[0]
        out['vtr'] = struct.unpack('<Q', bc[8:16])[0]
        accounts = (vm.get_account(key) for key in (CURVE, MTV, SOL_VAULT[0]))
        out['writable_accounts'] = [[a.lamports, str(a.owner), a.data.hex()] for a in accounts]
    return out


def cases():
    import random
    rng = random.Random(20261025)
    cs = []
    # randomized realistic + extreme grid
    for _ in range(60):
        cs.append(dict(rqr=rng.randint(1, 50) * 10**9, vtr=rng.randint(3, 20) * 10**14,
                       rtr=rng.randint(1, 9) * 10**14, tts=rng.randint(5, 40) * 10**14,
                       vqr=rng.randint(1, 9) * 10**10, vault=rng.randint(0, 30) * 10**12,
                       irtr=rng.choice([793_100_000_000_000, 500_000_000_000_000, 900_000_000_000_000]),
                       spl=rng.random() < 0.5, mayhem=True))
    base = dict(rqr=5_000_000_000, vtr=1_000_000_000_000_000, rtr=800_000_000_000_000, tts=1_000_000_000_000_000,
                vqr=30_000_000_000, vault=0, irtr=793_100_000_000_000, spl=False, mayhem=True)
    def ov(**k): d = dict(base); d.update(k); return d
    # edge cases
    cs += [ov(rqr=9_999_999), ov(rqr=10_000_000), ov(rqr=10_000_001),      # rqr write threshold
           ov(rqr=0), ov(rqr=1), ov(rqr=2_000_000),                        # below threshold -> no write
           ov(vtr=0), ov(rqr=5_000_000_000_000), ov(rqr=5_000_000_000_000, spl=True),  # caps engage
           ov(rqr=100_000_000_000), ov(rqr=100_000_000_000, spl=True),
           ov(mayhem=False), ov(mayhem=False, rqr=5_000_000_000_000),      # not mayhem -> no write
           ov(tts=300_000_000_000_000), ov(tts=400_000_000_000_000),       # den<=0 / den small
           ov(tts=300_000_000_000_000, rqr=1_000_000),                     # den<0 + below-threshold rqr
           ov(tts=300_000_000_000_000, mayhem=False),                      # not mayhem + den<0 -> no compute
           ov(vault=1_000_000_000_000_000), ov(vault=1_206_000_000_000_000),  # vault drives den small
           ov(vault=1_205_900_000_000_000), ov(vault=1_205_900_000_000_001),  # den == 1e12 (write) / 1e12-1 (skip)
           ov(spl=True), ov(irtr=500_000_000_000_000), ov(irtr=900_000_000_000_000)]
    return cs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    report_output = PumpReport(a.output, ROOT, a.candidate, __file__,
                               extra_inputs=(ORIGINAL, STUB, *DEPENDENCIES.values())) if a.output else None
    a.candidate = pin_program(a.candidate) if a.candidate else None
    original = pin_program(ORIGINAL)
    stub = pin_program(STUB)
    for path in DEPENDENCIES.values():
        pin_program(path)
    assert sha(original.read_bytes()) == '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
    rows, bad = [], []
    for i, c in enumerate(cases()):
        x = run(original, c)
        y = run(a.candidate, c) if a.candidate else None
        diff = [k for k in ('err', 'vqr', 'vtr', 'writable_accounts', 'events', 'logs') if y is not None and x.get(k) != y.get(k)]
        rows.append({'i': i, 'case': c, 'original': x, 'candidate': y, 'diff': diff})
        if diff:
            bad.append(i)
    report = {'scope': 'Synthetic-CPI-stub differential of pump set_mayhem_virtual_params; genuine invoke_signed, no bypass. No byte-identity claim.',
              'original_sha256': sha(original.read_bytes()),
              'candidate_sha256': sha(a.candidate.read_bytes()) if a.candidate else None,
              'stub_sha256': sha(stub.read_bytes()), 'cases': rows, 'mismatches': bad}
    if a.output:
        import gzip
        report_output.write(gzip.compress(json.dumps(report, indent=2).encode(), mtime=0))
    print(len(rows), 'cases', len(bad), 'mismatches')
    if bad:
        print('MISMATCHES at', bad[:10])
        for i in bad[:4]:
            r = rows[i]; print(' case', i, r['case']); print('   orig', r['original']); print('   cand', r['candidate'])
        raise SystemExit(1)


if __name__ == '__main__':
    main()
