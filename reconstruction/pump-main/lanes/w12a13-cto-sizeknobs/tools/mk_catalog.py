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
         'L1': {'pr': 2749, 'bytes': 27400, 'ratio': 0.45147, 'sha16': '784bea21ed580b15', 'first_store': None, 'genes': genes.BASES['L1']}}
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
    if not os.path.exists(K4SIZE):
        return out
    for l in open(K4SIZE):
        try:
            r = json.loads(l)
        except Exception:
            continue
        g = r.get('genes') or []
        if r.get('bytes') is None:
            continue
        if len(g) == 1:
            out.setdefault(('k4', g[0]), r)
        elif len(g) == 2 and g[0] == 's_bump_first':
            out.setdefault(('k4+s_bump_first', g[1]), r)
    return out


def main():
    res = load_res()
    k4s = k4size_rows()
    entries = {}
    for name, r in res.items():
        if not r.get('knobs') or len(r['knobs']) != 1:
            continue
        n = r['knobs'][0]
        b = r['base']
        e = entries.setdefault(n, {'name': n, 'category': CAT.get(n, 'other'), 'edit': edit_of(n), 'results': {}})
        if r.get('ok'):
            bb = BASES[b]
            fr = r.get('frame') if isinstance(r.get('frame'), dict) else {}
            e['results'][b] = {'bytes': r['bytes'], 'delta_bytes': r['bytes'] - bb['bytes'], 'ratio': r['ratio'],
                               'delta_ratio': round(r['ratio'] - bb['ratio'], 5), 'identical_to_base': r.get('sha') == bb['sha16'],
                               'first_store': fr.get('first_store'), 'losses': r['losses'],
                               'raw_losses': r['raw_losses_n'], 'calls': r.get('calls'), 'source': LANE}
        else:
            e['results'][b] = {'error': str(r.get('error'))[:300], 'source': LANE}
    for (b, n), r in k4s.items():
        e = entries.setdefault(n, {'name': n, 'category': CAT.get(n, 'other'), 'edit': edit_of(n), 'results': {}})
        bb = 27384 if b == 'k4' else 27392
        br = 0.4525 if b == 'k4' else 0.45094
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
    # markdown
    lines = ['| knob | category | main Δbytes | main Δratio | L1 Δbytes | L1 Δratio | k4 Δbytes | k4 Δratio |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    def cell(e, b, k):
        r = e['results'].get(b)
        if not r or 'error' in r:
            return 'fail' if r else ''
        v = r.get(k)
        if k == 'delta_bytes':
            return ('=' if r.get('identical_to_base') else f'{v:+d}')
        if k == 'delta_ratio':
            return '' if r.get('identical_to_base') else f'{v:+.5f}'
        return '' if v is None else str(v)
    for e in sorted(entries.values(), key=lambda e: (e['category'], e['name'])):
        if not any(b in e['results'] for b in ('main', 'L1', 'k4')):
            continue
        lines.append(f"| `{e['name']}` | {e['category']} | {cell(e,'main','delta_bytes')} | {cell(e,'main','delta_ratio')} | "
                     f"{cell(e,'L1','delta_bytes')} | {cell(e,'L1','delta_ratio')} | {cell(e,'k4','delta_bytes')} | {cell(e,'k4','delta_ratio')} |")
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
