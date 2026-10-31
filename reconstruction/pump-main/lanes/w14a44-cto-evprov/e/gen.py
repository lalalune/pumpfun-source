#!/usr/bin/env python3
"""gen.py: write e/<name>.py EDITS files for AdminCtoEvent provenance/order variants (line 767 literal + pargs/pre-lets).
Usage: gen.py name=tok,tok,... ...  tokens: hr_c hr_p ph cb_l mint_k nc_t nf_u auth_d sr_m sr_pre sr_pre2 ts_last ts_<field>
ts_pre ts_prepool ts_precurve ord_<perm-name> ..."""
import sys, os, json
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a44-cto-evprov/e')
LIT = 'let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};'
PARGS = 'let pargs=(target,a.bonding_curve.is_holder_reward,fee);'
POOLU = 'let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
CURVE = ' let (old_creator,old_fee)={\n'
NAMES = ['timestamp','authority','mint','bonding_curve','old_creator','new_creator','is_holder_reward','is_cashback_coin','old_creator_fee_bps','new_creator_fee_bps','sharing_config_reset','swept_to_holder_vault','pool_updated']
def build(toks):
    f = {'timestamp':'Clock::get()?.unix_timestamp','authority':'a.admin_set_creator_authority.key()','mint':'mint','bonding_curve':'a.bonding_curve.key()',
         'old_creator':'old_creator','new_creator':'a.bonding_curve.creator','is_holder_reward':'holder','is_cashback_coin':'a.bonding_curve.is_cashback_coin',
         'old_creator_fee_bps':'old_fee','new_creator_fee_bps':'a.bonding_curve.creator_fee_bps','sharing_config_reset':'sharing_update.is_some()',
         'swept_to_holder_vault':'swept','pool_updated':'pool_updated'}
    order = list(NAMES); edits = []; pre = ''; pargs = PARGS; poolu = POOLU; curve = CURVE
    for t in toks:
        if t == 'hr_c': f['is_holder_reward'] = 'a.bonding_curve.is_holder_reward'
        elif t == 'hr_p': f['is_holder_reward'] = 'pargs.1'
        elif t == 'hr_h2': f['is_holder_reward'] = 'holder==true'
        elif t == 'ph': pargs = 'let pargs=(target,holder,fee);'
        elif t == 'cb_l': f['is_cashback_coin'] = 'cashback'
        elif t == 'mint_k': f['mint'] = 'a.mint.key()'
        elif t == 'bc_k': f['bonding_curve'] = '*a.bonding_curve.to_account_info().key'
        elif t == 'nc_t': f['new_creator'] = 'target'
        elif t == 'nc_p': f['new_creator'] = 'pargs.0'
        elif t == 'nf_u': f['new_creator_fee_bps'] = 'fee.unwrap_or(old_fee)'
        elif t == 'nf_p': f['new_creator_fee_bps'] = 'pargs.2.unwrap_or(old_fee)'
        elif t == 'auth_d': f['authority'] = '*a.admin_set_creator_authority.key'
        elif t == 'sr_m': f['sharing_config_reset'] = 'matches!(sharing_update,Some(_))'
        elif t == 'sr_n': f['sharing_config_reset'] = '!sharing_update.is_none()'
        elif t == 'sr_pre':  # bool computed before curve update
            curve = ' let sr=sharing_update.is_some();let (old_creator,old_fee)={\n'; f['sharing_config_reset'] = 'sr'
        elif t == 'sr_prepool':
            poolu = 'let sr=sharing_update.is_some();' + POOLU; f['sharing_config_reset'] = 'sr'
        elif t == 'ts_pre': pre = 'let timestamp=Clock::get()?.unix_timestamp;'; f['timestamp'] = None
        elif t == 'ts_prepool': poolu = 'let timestamp=Clock::get()?.unix_timestamp;' + poolu; f['timestamp'] = None
        elif t == 'ts_postpool': poolu = poolu + 'let timestamp=Clock::get()?.unix_timestamp;'; f['timestamp'] = None
        elif t == 'ts_last': order.remove('timestamp'); order.append('timestamp')
        elif t.startswith('ts_at'):  # ts_at<k>: put timestamp at position k
            k = int(t[5:]); order.remove('timestamp'); order.insert(k, 'timestamp')
        elif t == 'ord_rev': order = ['timestamp'] + [x for x in reversed(NAMES) if x != 'timestamp']
        elif t == 'ord_revall': order = list(reversed(NAMES))
        elif t == 'ord_bools': # bools grouped after pubkeys
            order = ['timestamp','authority','mint','bonding_curve','old_creator','new_creator','is_holder_reward','is_cashback_coin','sharing_config_reset','pool_updated','old_creator_fee_bps','new_creator_fee_bps','swept_to_holder_vault']
        elif t == 'ord_hrcb':
            i, j = order.index('is_holder_reward'), order.index('is_cashback_coin'); order[i], order[j] = order[j], order[i]
        elif t.startswith('mv_'):  # mv_<field>_<k>
            _, fld, k = t.split('_', 2); fld = {'hr':'is_holder_reward','cb':'is_cashback_coin','sr':'sharing_config_reset','sw':'swept_to_holder_vault','pu':'pool_updated','of':'old_creator_fee_bps','nf':'new_creator_fee_bps','oc':'old_creator','nc':'new_creator','mi':'mint','au':'authority','bc':'bonding_curve'}[fld]
            order.remove(fld); order.insert(int(k), fld)
        else: raise SystemExit('bad tok ' + t)
    parts = []
    for n in order:
        v = f[n]
        if n == 'timestamp' and v is None: parts.append('timestamp')
        elif v == n: parts.append(n)
        else: parts.append(f'{n}:{v}')
    lit = pre + 'let e=AdminCtoEvent{' + ','.join(parts) + '};'
    if lit != LIT: edits.append((LIT, lit))
    if pargs != PARGS: edits.append((PARGS, pargs))
    if poolu != POOLU: edits.append((POOLU, poolu))
    if curve != CURVE: edits.append((CURVE, curve))
    return edits
for arg in sys.argv[1:]:
    name, spec = arg.split('=', 1)
    ed = build([t for t in spec.split(',') if t])
    open(f'{OUT}/{name}.py', 'w').write('EDITS=' + json.dumps(ed) + '\n')
    print(name, len(ed))
