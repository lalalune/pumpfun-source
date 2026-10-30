"""Focused cases selected from existing fixture tables or their public run APIs."""
import copy
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_create_quote_differential as create
import pump_create_control_differential as control
import pump_create_nested_differential as nested
import pump_fee_sweep_differential as sweep
import pump_v3_token_extensions_differential as v3
import pump_sell_v2_differential as sell


def manifest():
    rows = []
    tables = {name: module.cases() for name, module in
              [('create', create), ('control', control), ('nested', nested), ('sweep', sweep), ('v3', v3), ('sell', sell)]}
    def add(group, driver, label, case, origin, index=None, overrides=None):
        rows.append(dict(group=group, driver=driver, name=label, case=copy.deepcopy(case),
                         fixture_origin=origin, fixture_case_index=index, overrides=overrides))
    def named(group, driver, label):
        matches = [(i, row) for i, row in enumerate(tables[driver]) if row.get('case', row.get('name')) == label]
        assert len(matches) == 1, (driver, label)
        index, row = matches[0]
        add(group, driver, label, row, 'existing fixture table', index)
    def exact(group, driver, label, case):
        matches = [i for i, row in enumerate(tables[driver]) if row == case]
        assert matches, (driver, label, case)
        add(group, driver, label, tables[driver][matches[0]], 'existing fixture table', matches[0])
    def api(group, driver, label, case):
        add(group, driver, label, case, 'existing run API parameterization')

    for label in ['v2-base', 'optional-00', 'optional-000000000000000000',
                  'options-00ffffffffffffffff00', 'holder-zero-creator', 'zero-creator', 'disabled',
                  'name-byte-limit-32', 'name-byte-limit-33', 'symbol-byte-limit-13', 'symbol-byte-limit-14',
                  'uri-byte-limit-200', 'uri-byte-limit-201', 'prefund-bonding_curve-1',
                  'prefund-associated_bonding_curve-10000000', 'quote-False-0', 'quote-True-0', 'combined-creator-name']:
        named('create', 'create', label)
    for label in ['control-False-0', 'control-False-1', 'control-True-123456789',
                  'control-True-18446744073709551615', 'fee-300-1', 'fee-301-1',
                  'holder-fee', 'duplicate-entry', 'missing-entry']:
        named('create', 'control', label)
    for label in ['fresh', 'child-global-1087-0', 'child-global-1087-1',
                  'root-quote-1', 'creator-fee-300', 'creator-fee-301']:
        named('create', 'nested', label)

    native = dict(curve_quote=str(sweep.Pubkey.default()), quote=str(sweep.WSOL))
    token = dict(curve_quote=str(sweep.STABLE), quote=str(sweep.STABLE))
    wsol = dict(curve_quote=str(sweep.WSOL), quote=str(sweep.WSOL))
    for op in ['sweep_creator_fee', 'sweep_protocol_fee']:
        for mode, base in [('native', native), ('token', token), ('wsol', wsol)]:
            for label, extra in [('positive', {}), ('zero', dict(creator_fee=0, protocol_fee=0)),
                                 ('create_destination', dict(destination_missing=True))]:
                exact('sweep', 'sweep', f'{op}_{mode}_{label}', dict(base, op=op, **extra))
        for mode, base in [('native', native), ('token', token)]:
            exact('sweep', 'sweep', f'{op}_{mode}_low_rent', dict(base, op=op, curve_lamports=12344))
    exact('sweep', 'sweep', 'creator_token_missing_source', dict(token, op='sweep_creator_fee', source_missing=True))
    for mode, base in [('native', native), ('token', token)]:
        exact('sweep', 'sweep', 'creator_'+mode+'_maximum_fee', dict(base, creator_fee=2**64-1, protocol_fee=1))
    exact('sweep', 'sweep', 'creator_token2022_positive', dict(token, op='sweep_creator_fee', token22=True))
    for op in ['sweep_creator_fee', 'sweep_protocol_fee']:
        original = dict(token, op=op, creator_fee=0, protocol_fee=0,
                        patch={'associated_quote_bonding_curve': {'bytes': [(0, bytes(32).hex())]}})
        exact('sweep', 'sweep', op+'_zero_with_wrong_source_mint', original)

    common = dict(reserve_in=v3.base_in, reserve_out=v3.base_out, user_lamports=10**16)
    for op in ['buy_v3', 'buy_exact_quote_in_v3']:
        for mode in ['native', 'token', 'token2022']:
            base = dict(common, operation=op, amount=10**9, max_cost=10**12 if op == 'buy_v3' else 1)
            if mode != 'native':
                base.update(token_quote=True, quote2022=mode == 'token2022', replace=13)
            for label, extra in [('positive', {}), ('zero', dict(amount=0)),
                                 ('slippage', dict(max_cost=0 if op == 'buy_v3' else 10**12)),
                                 ('complete', dict(mutation='complete'))]:
                api('v3', 'v3', f'{op}_{mode}_{label}', dict(base, **extra))
    for amount in [499999999, 500000000, 500000001]:
        api('v3', 'v3', 'buy_v3_native_crossing_'+str(amount),
            dict(common, operation='buy_v3', amount=amount, max_cost=10**12, real_base=500000000))
    for label in ['buy_v3_0_1_False', 'buy_v3_100_1_False',
                  'buy_exact_quote_in_v3_limit_33867943546787', 'buy_exact_quote_in_v3_limit_33867943546789']:
        named('v3', 'v3', label)
    for fees in [[0, 0, 0], [10000, 0, 5000], [2**64-1, 0, 5000]]:
        api('v3', 'v3', 'buy_v3_native_fees_'+str(fees),
            dict(common, operation='buy_v3', amount=10**9, max_cost=10**12, fees=fees))
    api('v3', 'v3', 'buy_complete_and_wrong_buyback',
        dict(common, operation='buy_v3', amount=10**9, max_cost=10**12, flags=[48], mutation='wrong_buyback'))
    api('v3', 'v3', 'buy_cashback_and_wrong_quote_user',
        dict(common, operation='buy_v3', amount=10**9, max_cost=10**12, flags=[82], token_quote=True,
             quote2022=True, replace=13, quote_mutation='user_authority'))
    api('v3', 'v3', 'exact_zero_and_wrong_fee_owner',
        dict(common, operation='buy_exact_quote_in_v3', amount=0, max_cost=1, mutation='fee_owner'))
    api('v3', 'v3', 'exact_cashback_and_truncated_quote_fee',
        dict(common, operation='buy_exact_quote_in_v3', amount=10**9, max_cost=1, flags=[82],
             token_quote=True, quote2022=True, replace=13, extension=True, bps=100, mint_length=170))

    for label in ['native', 'token', 'token22', 'zero', 'slippage']:
        named('sell', 'sell', label)
    api('sell', 'sell', 'token_zero', dict(token_quote=True, amount=0))
    api('sell', 'sell', 'token2022_slippage', dict(token_quote=True, token22=True, minimum=10**12))
    for is_token in [False, True]:
        for amount in [1, 10**9, 10**9+1]:
            named('sell', 'sell', f'amount_{is_token}_[]_{amount}')
    for minimum in [13664, 13665, 13666]:
        named('sell', 'sell', 'transfer_fee_100_minimum_'+str(minimum))
    for maximum in [0, 1, 7]:
        named('sell', 'sell', 'transfer_fee_cap_'+str(maximum))
    for label in ['sharing_native', 'sharing_token', 'cashback', 'holder']:
        named('sell', 'sell', label)
    api('sell', 'sell', 'zero_and_wrong_buyback', dict(amount=0, wrong_keys=['buyback_fee_recipient']))
    assert len(rows) == len({(row['group'], row['name']) for row in rows})
    counts = {group: sum(row['group'] == group for row in rows) for group in ['create', 'sweep', 'v3', 'sell']}
    assert counts == dict(create=33, sweep=28, v3=38, sell=24), counts
    return rows


if __name__ == '__main__':
    rows = manifest()
    print(json.dumps(dict(counts={group: sum(row['group'] == group for row in rows)
                                  for group in ['create', 'sweep', 'v3', 'sell']}, cases=rows), indent=2))
