#!/usr/bin/env python3
"""Differential for the is_cashback_coin branch of pump's v3 trade handlers.

TASK NOTE / FINDING: this oracle was written to recover a claimed cashback-ACCEPT
branch in buy_v3/sell_v3 (accrual into the user_volume_accumulator). Driving the
captured ORIGINAL binary (evidence/original/pump/deployed.so) as the differential
oracle shows there is NO accept branch in v3: on a bonding curve with
is_cashback_coin=true the original REJECTS with CashbackCoinNotSupported (6094) at
programs/pump/src/trade_v3.rs:150, on BOTH the SOL and the USDC/Token-2022 quote
paths, for buy_v3, sell_v3 and buy_exact_quote_in_v3. The cashback-ACCEPT accrual
is a v2/legacy feature (buy_v2/sell_v2/legacy_buy/legacy_sell), already implemented
and consistent with claim_cashback; the decompiled helper at 0x6cd78 (errors
6072/6073/6076) carries "programs/pump/src/sell_v2.rs" / "sell.rs" strings, i.e. it
belongs to the v2 path, not v3.

This oracle therefore validates the GENUINE behavior: the reconstruction's v3
handlers must reject a cashback coin byte-identically to the original, while
non-cashback v3 trades are unchanged. It builds on the v3 token-extensions fixture
(same synthetic state, genuine dependency CPIs, real verified signatures)."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
import argparse,gzip,hashlib,json
import pump_v3_token_extensions_differential as v3
import pump_trade_fixture as f

# is_cashback_coin is byte 82 of the bonding-curve account (disc[8] + payload:
# complete@48, creator@49..81, is_mayhem_mode@81, is_cashback_coin@82).
CASHBACK_FLAG = 82


def cases():
    rows = []
    for op in ['buy_v3', 'sell_v3', 'buy_exact_quote_in_v3']:
        amount = 500000000 if op == 'sell_v3' else 10**9
        max_cost = 0 if op == 'sell_v3' else (1 if op == 'buy_exact_quote_in_v3' else 10**12)
        # --- SOL quote ---
        sol = {'operation': op, 'amount': amount, 'max_cost': max_cost,
               'reserve_in': v3.base_in, 'reserve_out': v3.base_out, 'user_lamports': 10**16}
        rows.append({**sol, 'name': f'{op}_sol_noncashback'})           # control: unchanged
        rows.append({**sol, 'name': f'{op}_sol_cashback', 'flags': [CASHBACK_FLAG]})  # rejects 6094
        # cashback coin + a second curve flag, to show the gate precedes other logic
        rows.append({**sol, 'name': f'{op}_sol_cashback_mayhem', 'flags': [CASHBACK_FLAG, 81]})
        # --- USDC / Token-2022 quote ---
        tok = {**sol, 'token_quote': True, 'quote2022': True, 'replace': 13}
        rows.append({**tok, 'name': f'{op}_usdc_noncashback'})          # control: unchanged
        rows.append({**tok, 'name': f'{op}_usdc_cashback', 'flags': [CASHBACK_FLAG]})  # rejects 6094
        rows.append({**tok, 'name': f'{op}_usdc_cashback_tfee', 'flags': [CASHBACK_FLAG],
                     'extension': True, 'bps': 100})
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=f.pathlib.Path)
    p.add_argument('--output', type=f.pathlib.Path, required=True)
    a = p.parse_args()
    original = f.R / 'evidence/original/pump/deployed.so'
    rows, bad = [], []
    for i, c in enumerate(cases()):
        x = v3.run(str(original), c)
        y = v3.run(str(a.candidate), c) if a.candidate else None
        match = (all(x[k] == y[k] for k in ['error', 'accounts', 'inner_instructions',
                                            'event_payloads', 'return_data']) if y else None)
        rows.append({'case': c, 'original_error': x['error'],
                     'candidate_error': (y['error'] if y else None), 'match': match})
        if match is False:
            bad.append(i)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        'scope': ('v3 cashback-coin gate differential. The original REJECTS cashback coins '
                  'in v3 (CashbackCoinNotSupported @ trade_v3.rs:150); there is no accept '
                  'branch to recover. Synthetic v3 state, genuine dependency CPIs, real '
                  'verified signatures. Full binary equality not claimed.'),
        'original_sha256': sha(original),
        'candidate_sha256': sha(a.candidate) if a.candidate else None,
        'harness_sha256': sha(f.pathlib.Path(__file__)),
        'v3_harness_sha256': sha(f.pathlib.Path(v3.__file__)),
        'fixture_import_sha256': sha(f.pathlib.Path(f.__file__)),
        'case_count': len(rows), 'cases': rows, 'mismatches': bad}
    raw = (json.dumps(report, indent=2) + '\n').encode()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(gzip.compress(raw, mtime=0) if a.output.suffix == '.gz' else raw)
    print(json.dumps({'cases': len(rows), 'mismatches': bad}))
    assert not bad


if __name__ == '__main__':
    main()
