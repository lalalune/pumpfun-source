#!/usr/bin/env python3
"""mk_catalog.py: build sizeknobs-cto.json + a markdown table from this lane's trials, prior ledger rows and
the w12a04-cto-k4size lane's k4-base results (credited)."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import knobs, genes

LANE = 'w12a13-cto-sizeknobs'
OUT = os.path.expanduser(f'~/.cache/pumpfun-reconstruction/lanes/{LANE}')
K4SIZE = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a04-cto-k4size/r1.jsonl')
DEST_JSON = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'
BASES = {'main': {'commit': '20a1ae9c0', 'bytes': 27400, 'ratio': 0.43919, 'sha16': '8cd7695c3fc638fc', 'first_store': -2288},
         'k4': {'bytes': 27384, 'ratio': 0.4525, 'sha16': '07c7e215dbe32e7b', 'first_store': -2288,
                'genes': genes.BASES['k4']},
         'j3': {'bytes': 27312, 'ratio': 0.45251, 'sha16': 'a0a2d2146fd9b1b8', 'genes': genes.BASES['j3']},
         'L1': {'pr': 2749, 'bytes': 27400, 'ratio': 0.45147, 'sha16': '784bea21ed580b15', 'first_store': None, 'genes': genes.BASES['L1']},
         'L2': {'bytes': 27400, 'ratio': 0.45177, 'sha16': '6892c2a15de3ba6a', 'genes': genes.BASES['L2']},
         'C2': {'bytes': 27392, 'ratio': 0.45213, 'sha16': 'af95f0c58856b50c', 'genes': genes.BASES['C2']},
         'C3': {'bytes': 27384, 'ratio': 0.47618, 'sha16': 'cabdd7a55d964b6a', 'genes': genes.BASES['C3']},
         'Av': {'bytes': 27392, 'ratio': 0.48569, 'sha16': None, 'from': 'w12a14-cto-hillclimb b53cbd23e405 (K5+amm_cb_local+k4_oldfee_after+v326_match)'},
         'A2': {'bytes': 27384, 'ratio': 0.48607, 'sha16': None, 'from': 'w12a14-cto-hillclimb 6f262fb34c9e (Av + a2_orig_order)'},
         'D': {'bytes': 27400, 'ratio': 0.48652, 'sha16': None, 'from': 'w12a14-cto-hillclimb d7acbb3d549a = #2831'},
         'M2': {'bytes': 27400, 'ratio': 0.48742, 'sha16': None, 'from': 'main 1905fba85 (#2831 + w12b12 nested pool seeds)'}}
ORIG_FIRST_STORE = -2344

CAT = {}
for n in ['sh_key_borrow', 'val_sh_borrow', 's_dest_borrow', 's_old_borrow', 'w_ev_creator_borrow', 'p_ev_auth_borrow', 'v_ik_borrow', 'p_share_ref']:
    CAT[n] = 'copied-vs-borrowed Pubkey'
for n in ['val_match', 'prep_match', 'w_frozen_match', 's_tok_amt_match', 's_ensure_match', 'w_coin_cpi_match', 'p_pool_match']:
    CAT[n] = '? vs explicit match'
for n in ['v_ik_split', 'v_fee_split', 'v_fee_range', 'm_src_frozen_short']:
    CAT[n] = 'combined vs split check'
for n in ['v_new_match', 'v_new_okor', 'v_mayhem_req', 'w_writable_req', 'v_new_issome']:
    CAT[n] = 'early-return form'
for n in ['s_rent_local', 's_amm_let', 's_amm_empty_let', 'w_ev_ts_let', 'p_ev_ts_let', 'tgt_shadow_drop', 's_bump_inline', 'p_pb_inline', 'hk_dot0', 's_dest_tuple']:
    CAT[n] = 'let binding'
for n in ['sh_owner_first', 'sh_empty_mid', 'st_ql_first', 'st_global_first', 'w_ev_creator_first', 'p_ev_mint_first', 'p_ev_ts_last', 'm_co_order',
          'm_coin_first', 's_frozen_first', 'g_old_fee_first', 's_bump_first', 'p_hr_before_creator', 'p_cb_before_hr', 'w_create_rev',
          's_tok_create_rev', 's_tcf_rev', 'w_coin_cpi_rev', 'g_canedit_first']:
    CAT[n] = 'statement / evaluation order'
for n in ['sh_key_rev', 'cb_rev', 'v_hr_rev', 'v_ik_rev', 'v_cb_rev', 's_native_rev', 'w_native_rev', 's_dest_rev', 'hold_rev', 'm_target_if_rev', 'v_he_demorgan']:
    CAT[n] = 'operand order / polarity'
for n in ['L_canedit_revert', 'L_feeunwrap_revert', 'L_fee_match', 'L_fee_unwrap_again', 'L_canedit_revert+L_fee_match',
          'L_canedit_revert+L_feeunwrap_revert', 'L_canedit_revert+L_feeunwrap_revert+v_fee_match', 'p_canedit_revert', 'p_feeunwrap_revert',
          'p_oldfee_revert', 'p_canedit_after_creator', 'p_cb_before_hr']:
    CAT[n] = 'curve-store form'
for n in ['v_fee_match', 'w_collect_match', 'L_share_none_first', 'p_su_match', 'L_canedit_revert+w_collect_match', 'D_fee_none_first']:
    CAT[n] = 'if let vs match'
for n in ['p_pb_inline', 's_bump_inline', 'L_bump_inline', 'p_pb_inline+s_bump_inline']:
    CAT[n] = 'seed bump inline'
for n in ['D_holder_phi']:
    CAT[n] = 'gene (other lane)'
for n in ['hold_unwrap', 'hold_matches', 'cb_bitand', 's_satsub', 's_amt_ne', 's_tok_ne', 'w_owner_deref', 'sh_owner_deref', 'p_pool_owner_deref',
          'm_su_then', 'p_share_match', 'p_pool_with_signer', 'g_fee_unwrap', 'g_region2_tree', 'p_ctx_a_reborrow', 'p_pool_empty_first']:
    CAT[n] = 'expression form'

# Prior measurements on an admin_cto.rs identical to main 20a1ae9c0 (h1 = #2642), from the shared ledger.
PRIOR_MAIN = [
    ('wallet_flags', 'genes.G wallet_flags (#2518 do_collect/do_coin)', -88, 0.45251, 'w9r2-admincto-harvest j3 (re-measured here)'),
    ('g_region2_tree', 'sharing_update/collect_old as one if-tree (#2515)', +16, 0.43995, 'w9r2-admincto-harvest j5'),
    ('g_fee_unwrap', 'curve.creator_fee_bps=fee.unwrap_or(old_fee)', +8, 0.43822, 'w9r2-admincto-sibling h4'),
    ('g_canedit_first', 'curve.can_edit_creator_fee=false right after the old reads', +48, 0.43969, 'w9r2-admincto-sibling h3'),
    ('p_pool_empty_first', 'pool_updated tests !data_is_empty() first', 0, 0.43859, 'w9r2-admincto-harvest i4'),
    ('p_hr_before_creator', 'is_holder_reward stored before creator (#2621)', 0, 0.43919, 'w9r2-admincto-harvest i1 (same ratio/slots)'),
    ('cashback_late', 'cashback computed at the curve store (!holder&&cashback)', -104, 0.30977, 'w9r2-admincto-harvest j1'),
    ('with_signer_sharing', 'sharing CPI CpiContext::new(..).with_signer(..)', +24, 0.40844, 'w9r2-admincto-harvest j2'),
    ('errseq_target', 'validate returns st.creator when shared (#2564)', -24, 0.28893, 'w9r2-admincto-harvest j4'),
    ('holder_unwrap_and', 'holder.unwrap_or(false) + cashback with & (#2550)', -184, 0.4371, 'w9r2-admincto-harvest j6'),
    ('fee_range_sibling', 'if !(f>0&&f<=st.max_fee) (pump-amm sibling spelling)', 0, 0.43919, 'w9r2-admincto-sibling v3 (byte-identical)'),
    ('rent_named', 'sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0);', +16, 0.43816, 'w12a11-cto-sibling sib-rent-local'),
    ('cpi_sws', 'sharing CPI with_signer (re-measured)', +24, 0.40844, 'w12b12-cto-cpi cpi-sws'),
    ('cpi_seeds_inline', 'signer seeds as inline literal in both signed CPIs (no pb/poolseeds/signer_seeds locals)', +184, 0.39982, 'w12b12-cto-cpi seedsinline'),
]
PRIOR_K4 = [
    ('rent_named', 'sweep native arm named Rent local', -32, 0.45217, 'w12a11-cto-sibling sib-k4-rent-local'),
    ('s_bump_first', 'sweep binds bump before old (l1)', +8, 0.45094, 'w9r2-admincto-harvest l1'),
    ('p_hr_before_creator', 'curve.creator stored after is_holder_reward (l2)', -48, 0.45231, 'w9r2-admincto-harvest l2'),
    ('p_pool_empty_first', 'pool_updated tests !data_is_empty() first (l3)', -8, 0.45197, 'w9r2-admincto-harvest l3'),
    ('g_region2_tree_revert', 'k4 without region2_tree (l4)', -16, 0.45174, 'w9r2-admincto-harvest l4'),
]


def edit_of(n):
    if n in knobs.K:
        return [{'old': a, 'new': b} for a, b in knobs.K[n]]
    if n in genes.G:
        return [{'old': a, 'new': b} for a, b in genes.G[n]]
    return None


def load_res():
    rows = {}
    for f in glob.glob(f'{OUT}/res/*.json'):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if 'name' in r and 'knobs' in r:
            rows[r['name']] = r
    return rows


def k4size_rows():
    out = {}
    lines = []
    for f in (K4SIZE, K4SIZE.replace('r1.jsonl', 'r2.jsonl')):
        if os.path.exists(f):
            lines += open(f).read().splitlines()
    for l in lines:
        try:
            r = json.loads(l)
        except Exception:
            continue
        nm = r.get('name', '')
        if nm.startswith('L1.') and len(r.get('genes') or []) == 1 and r.get('bytes'):
            out.setdefault(('L1', r['genes'][0]), r)
        elif nm.startswith('L2.') and len(r.get('genes') or []) == 1 and r.get('bytes'):
            out.setdefault(('L2', r['genes'][0]), r)
    for l in lines:
        try:
            r = json.loads(l)
        except Exception:
            continue
        g = r.get('genes') or []
        if r.get('bytes') is None:
            continue
        if len(g) == 1 and r.get('name', '').startswith('s.'):
            out.setdefault(('k4', g[0]), r)
        elif len(g) == 2 and g[0] == 's_bump_first' and r.get('name', '').startswith('b.'):
            out.setdefault(('k4+s_bump_first', g[1]), r)
    return out


def main():
    res = load_res()
    k4s = k4size_rows()
    entries = {}
    for name, r in res.items():
        if not r.get('knobs'):
            continue
        n = r['knobs'][0] if len(r['knobs']) == 1 else '+'.join(r['knobs'])
        b = r['base']
        b = 'Av' if b.endswith('Av_b53cbd.rs') else 'A2' if b.endswith('A2_6f262f.rs') else 'D' if b.endswith('D_d7acbb.rs') else 'M2' if b.endswith('main_now.rs') else b
        e = entries.setdefault(n, {'name': n, 'category': CAT.get(n, 'other'), 'edit': edit_of(n), 'results': {}})
        if r.get('ok'):
            bb = BASES[b]
            fr = r.get('frame') if isinstance(r.get('frame'), dict) else {}
            e['results'][b] = {'bytes': r['bytes'], 'delta_bytes': r['bytes'] - bb['bytes'], 'ratio': r['ratio'],
                               'delta_ratio': round(r['ratio'] - bb['ratio'], 5),
                               'identical_to_base': (r.get('sha') == bb['sha16']) if bb.get('sha16') else (r['bytes'] == bb['bytes'] and r['ratio'] == bb['ratio']),
                               'first_store': fr.get('first_store'), 'losses': r['losses'],
                               'raw_losses': r['raw_losses_n'], 'calls': r.get('calls'), 'source': LANE}
        else:
            e['results'][b] = {'error': str(r.get('error'))[:300], 'source': LANE}
    for (b, n), r in k4s.items():
        e = entries.setdefault(n, {'name': n, 'category': CAT.get(n, 'other'), 'edit': edit_of(n), 'results': {}})
        bb, br = {'k4': (27384, 0.4525), 'k4+s_bump_first': (27392, 0.45094), 'L1': (27400, 0.45147), 'L2': (27400, 0.45177)}[b]
        e['results'].setdefault(b, {'bytes': r['bytes'], 'delta_bytes': r['bytes'] - bb, 'ratio': r['ratio'],
                                    'delta_ratio': round(r['ratio'] - br, 5), 'source': 'w12a04-cto-k4size (their gene names)'})
    prior = [{'name': n, 'desc': d, 'delta_bytes': db, 'ratio': ra, 'delta_ratio': round(ra - 0.43919, 5), 'source': s} for n, d, db, ra, s in PRIOR_MAIN]
    cat = {'lane': LANE, 'target': '0x22a10 admin_cto::execute (programs/pump/src/creator/admin_cto.rs)',
           'pinned_bytes': 27400, 'orig_first_store': ORIG_FIRST_STORE,
           'bases': BASES,
           'how_to_read': ('delta_bytes/delta_ratio are against the named base build. Sizes are NOT additive: always re-measure a '
                           'combination. identical_to_base=true means the unstripped .so sha equals the base (no codegen change). '
                           'first_store is the first [r10-X] spill offset in admin_cto::execute (frame proxy; original -2344, ours -2288). '
                           'Every knob keeps the newline count and every error/require/msg site on its line.'),
           'knobs': sorted(entries.values(), key=lambda e: (e['category'], e['name'])),
           'prior_on_main_from_ledger': prior,
           'prior_on_k4_from_ledger': [{'name': n_, 'desc': d_, 'delta_bytes': db_, 'ratio': ra_, 'source': s_} for n_, d_, db_, ra_, s_ in PRIOR_K4]}
    json.dump(cat, open(f'{OUT}/sizeknobs-cto.json', 'w'), indent=1)
    if '--publish' in sys.argv:
        json.dump(cat, open(DEST_JSON, 'w'), indent=1)
    # markdown (long format: one row per measured knob x base)
    lines = ['| knob | category | base | Δbytes | Δratio | ratio | first spill | calls | measured by |',
             '| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |']
    order = {'main': 0, 'L1': 1, 'L2': 2, 'C2': 3, 'C3': 4, 'Av': 5, 'A2': 6, 'D': 7, 'M2': 8, 'k4': 9, 'k4+s_bump_first': 10}
    for e in sorted(entries.values(), key=lambda e: (e['category'], e['name'])):
        for bname, r in sorted(e['results'].items(), key=lambda kv: order.get(kv[0], 99)):
            if 'error' in r:
                lines.append(f"| `{e['name']}` | {e['category']} | {bname} | fail | | | | | {r.get('source','')} |")
                continue
            db = '=' if r.get('identical_to_base') else f"{r['delta_bytes']:+d}"
            dr = '' if r.get('identical_to_base') else f"{r['delta_ratio']:+.5f}"
            fs = r.get('first_store'); fs = f"-0x{-fs:x}" if isinstance(fs, int) else ''
            calls = '+'.join(str(x) for x in r['calls']) if r.get('calls') else ''
            src = 'here' if r.get('source') == LANE else 'w12a04'
            lines.append(f"| `{e['name']}` | {e['category']} | {bname} | {db} | {dr} | {r['ratio']} | {fs} | {calls} | {src} |")
    lines += ['', '| prior knob on main (ledger; admin_cto.rs identical to main 20a1ae9c0) | Δbytes | ratio | Δratio | source |', '| --- | ---: | ---: | ---: | --- |']
    for p_ in prior:
        lines.append(f"| {p_['desc']} | {p_['delta_bytes']:+d} | {p_['ratio']} | {p_['delta_ratio']:+.5f} | {p_['source']} |")
    lines += ['', '| prior knob on k4 (ledger) | Δbytes | ratio | Δratio | source |', '| --- | ---: | ---: | ---: | --- |']
    for n_, d_, db_, ra_, s_ in PRIOR_K4:
        lines.append(f"| {d_} | {db_:+d} | {ra_} | {ra_-0.4525:+.5f} | {s_} |")
    k4b = [(n_, r_) for (b_, n_), r_ in k4s.items() if b_ == 'k4+s_bump_first']
    if k4b:
        lines += ['', '| w12a04-cto-k4size knob on k4+s_bump_first (27,392 / 0.45094) | Δbytes | ratio | Δratio |', '| --- | ---: | ---: | ---: |']
        for n_, r_ in sorted(k4b):
            lines.append(f"| `{n_}` | {r_['bytes']-27392:+d} | {r_['ratio']} | {r_['ratio']-0.45094:+.5f} |")
    open(f'{OUT}/sizeknobs-table.md', 'w').write('\n'.join(lines) + '\n')
    print(f'{len(entries)} knobs; wrote {OUT}/sizeknobs-cto.json and sizeknobs-table.md')


if __name__ == '__main__':
    main()
