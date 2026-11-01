#!/usr/bin/env python3
"""delta.py: writes relay/DELTA.json and relay/DELTA.md.
Compares the live ELF with (a) the old source rebuilt on platform-tools v1.54, the meaningful comparison, because the toolchain changed;
(b) the old deployed ELF, built with v1.48; (c) the current skeleton build (open work).
Usage: delta.py <old-source-on-v154/unstripped.so> <skeleton/unstripped.so> <old-measured/symbols.so>
"""
import sys, os, json, hashlib, collections, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relay
from relaylib import Elf, symbols, demangle, toks
R = relay.R
old154, skel, oldsym = sys.argv[1:4]
OPEN = {  # target addr: (reading, cluster)
 0x18478: ('distribute_after_just_swapping prechecks (shared with exact)', 'C1-distribute-bps'), 0x18af0: ('distribute_after_just_swapping_v1 handler', 'C1-distribute-bps'),
 0x1a6d8: ('distribute_after finish: reload, burn_and_close (shared with exact)', 'C1-distribute-bps'), 0x1b090: ('distribute_non_swap prechecks (shared with exact)', 'C1-distribute-bps'),
 0x1b810: ('distribute_non_swap_output_mint_v1 handler', 'C1-distribute-bps'), 0x1d2d0: ('distribute_non_swap finish: reload, burn_and_close (shared with exact)', 'C1-distribute-bps'),
 0x24578: ('tools::distribution::shared::distribute', 'C1-distribute-bps'), 0x25f00: ('tools::distribution::shared transfer worker (bps)', 'C1-distribute-bps'),
 0x20580: ('admit_bridge_payment handler body', 'C3-bridge-handlers'), 0x21608: ('recover_bridge_payment handler body', 'C3-bridge-handlers'),
 0x933a0: ('#[program] recover_bridge_payment_v1 wrapper', 'C3-bridge-handlers'),
 0x19c80: ('distribute_exact_after_just_swapping_v1 handler', 'C2-distribute-exact'), 0x1c878: ('distribute_exact_non_swap_output_mint_v1 handler', 'C2-distribute-exact'),
 0x24ec0: ('tools::distribution::shared exact distribution', 'C2-distribute-exact'), 0x27048: ('tools::distribution::shared exact transfer worker', 'C2-distribute-exact'),
 0x8eb0: ('drop_in_place of the 4 AccountInfo clones in distribution CPIs', 'C2-distribute-exact'),
 0x11668: ('cpi::jupiter::invoke_jupiter', 'C4-jupiter-swap'), 0x11f80: ('cpi::jupiter::swap_observed', 'C4-jupiter-swap'), 0x1ec18: ('swap_then_distribute_v1 handler', 'C4-jupiter-swap'),
 0x28e48: ('tools::donate::shared::donate_shared', 'C5-donate'), 0x29ca8: ('tools::donate::shared signed transfer core (called by donate_shared and admit)', 'C5-donate'),
 0x23230: ('tools::checks::typed_mint_safe', 'C6-checks'), 0x227e8: ('tools::checks native mint for program', 'C6-checks'), 0x22b78: ('tools::checks::native_mint_pair', 'C6-checks'),
 0x1590: ('anchor_lang::error::Error::with_values, third instance (14 try_accounts closures call it)', 'C7-framework-layout'),
 0xb3278: ('alloc::raw_vec::RawVec<T,A>::grow_one (spl_token::instruction::transfer_checked)', 'C7-framework-layout'), 0xbcac0: ('alloc::raw_vec::finish_grow, separate instance', 'C7-framework-layout'),
}
t = Elf(relay.TARGET); tf = relay.target_table(t); tsz = dict(tf)
tn = {a: t.norm(a, s) for a, s in tf}
def table(path):
    e = Elf(path); sy = symbols(path)
    n = {a: e.norm(a, v[0]) for a, v in sy.items()}
    idx = collections.defaultdict(list)
    for a, v in sorted(sy.items()):
        idx[(v[0], hashlib.sha1(n[a][0]).digest())].append(a)
    return e, sy, n, idx
def exact(idx):
    used = set(); pair = {}
    for a, s in tf:
        k = (s, hashlib.sha1(tn[a][0]).digest())
        free = [x for x in idx.get(k, ()) if x not in used]
        if free:
            pair[a] = free[0]; used.add(free[0])
    return pair, used
e4, s4, n4, i4 = table(old154); p4, u4 = exact(i4)
eS, sS, nS, iS = table(skel); pS, uS = exact(iS)
eO, sO, nO, iO = table(oldsym); pO, uO = exact(iO)
T = {a: toks(tn[a][0]) for a, _ in tf}
free4 = {a for a in s4 if a not in u4}
byname = collections.defaultdict(list)
for a in free4:
    byname[demangle(s4[a][1])].append(a)
rows = []; mod_used = set()
order = sorted((a for a, _ in tf if a not in p4), key=lambda a: -tsz[a])
sim = {}
for a in order:
    nm = demangle(sS[pS[a]][1]) if a in pS else OPEN.get(a, ('?', None))[0]
    cands = [b for b in free4 if b not in mod_used and 0.25 <= s4[b][0] / max(1, tsz[a]) <= 4]
    best = (0, None)
    named = [b for b in byname.get(nm, []) if b not in mod_used]
    for b in (named or cands):
        tb = toks(n4[b][0])
        q = difflib.SequenceMatcher(None, T[a], tb, autojunk=False).quick_ratio()
        if q > best[0]:
            r = difflib.SequenceMatcher(None, T[a], tb, autojunk=False).ratio()
            if r > best[0]:
                best = (r, b)
    if best[1] is not None and best[0] >= (0.05 if named else 0.30):
        sim[a] = best; mod_used.add(best[1])
strs_ro = relay.Ro(t)
for a, s in tf:
    st = 'identical' if a in p4 else ('modified' if a in sim else 'added')
    name = demangle(sS[pS[a]][1]) if a in pS else OPEN.get(a, ('?', None))[0]
    txt = []
    for v in tn[a][3]:
        x = strs_ro.text(v, 60)
        if x and x not in txt:
            txt.append(x)
    rows.append({'addr': hex(a), 'size': s, 'status': st, 'name': name, 'skeleton_match': a in pS, 'cluster': OPEN.get(a, (None, None))[1],
                 'old_v154_symbol': demangle(s4[p4[a]][1]) if a in p4 else (demangle(s4[sim[a][1]][1]) if a in sim else None), 'similarity': round(sim[a][0], 3) if a in sim else (1.0 if a in p4 else 0),
                 'identical_to_old_binary': hex(pO[a]) if a in pO else None, 'calls': len(tn[a][1]), 'syscalls': sorted(set(tn[a][2])), 'strings': txt[:5]})
removed = [{'old_v154_addr': hex(a), 'size': s4[a][0], 'name': demangle(s4[a][1])} for a in sorted(free4 - mod_used, key=lambda a: -s4[a][0])]
removed_old_bin = [{'old_addr': hex(a), 'size': v[0], 'name': demangle(v[1])} for a, v in sorted(sO.items()) if a not in uO]
cnt = collections.Counter(r['status'] for r in rows); bytes_ = collections.Counter()
for r in rows:
    bytes_[r['status']] += r['size']
summary = {'target_functions': len(rows), 'target_text_bytes': sum(r['size'] for r in rows), 'status_vs_old_source_on_v154': dict(cnt), 'status_bytes': dict(bytes_), 'removed_vs_old_source_on_v154': len(removed),
           'identical_to_old_binary_v148': sum(1 for r in rows if r['identical_to_old_binary']), 'old_binary_functions': len(sO), 'old_binary_functions_without_identical_partner': len(removed_old_bin),
           'skeleton_matched': sum(1 for r in rows if r['skeleton_match']), 'skeleton_matched_bytes': sum(r['size'] for r in rows if r['skeleton_match'])}
clusters = collections.OrderedDict()
for r in sorted((r for r in rows if r['cluster']), key=lambda r: r['cluster']):
    c = clusters.setdefault(r['cluster'], {'bytes': 0, 'functions': []}); c['bytes'] += r['size']; c['functions'].append(r['addr'])
json.dump({'summary': summary, 'clusters': clusters, 'functions': rows, 'removed': removed, 'old_binary_without_partner': removed_old_bin}, open(R + '/DELTA.json', 'w'), indent=0)
L = ['# Donation Relay: delta between the live program and the old source', '', '`DELTA.json` holds the same rows with more fields. Boundaries come from `relaylib.Elf.functions()`, which reproduces all 492 symbols of the old build exactly (no extras, no misses, same sizes).', '',
     '## Summary', '', '| | functions | .text bytes |', '|---|---:|---:|']
for k in ('identical', 'modified', 'added'):
    L.append(f'| {k}, against the old source rebuilt on v1.54 | {cnt[k]} | {bytes_[k]:,} |')
L += [f"| removed: old source functions on v1.54 with no partner | {len(removed)} | {sum(x['size'] for x in removed):,} |",
      f"| new functions identical to a function of the old deployed ELF (v1.48) | {summary['identical_to_old_binary_v148']} of {len(rows)} | |",
      f"| matched by the current skeleton (`swarm/w20-relay-scout`) | {summary['skeleton_matched']} of {len(rows)} | {summary['skeleton_matched_bytes']:,} of {summary['target_text_bytes']:,} |", '',
      '`identical` means same length and same bytes after masking internal call immediates and relocated lddw values, the same normalization the scorer uses. Most of the difference from the old deployed ELF is the compiler (v1.48 to v1.54), not the source.', '',
      '## Open functions, by cluster', '', '| cluster | target addr | size | status | reading | similarity to old source function |', '|---|---|---:|---|---|---:|']
for r in sorted((r for r in rows if not r['skeleton_match']), key=lambda r: (r['cluster'] or '', int(r['addr'], 16))):
    L.append(f"| {r['cluster']} | `{r['addr']}` | {r['size']} | {r['status']} | {r['name']} | {r['similarity']} |")
L += ['', '## Removed against the old source on v1.54', '', '| old-source-on-v1.54 addr | size | name |', '|---|---:|---|']
for x in removed:
    L.append(f"| `{x['old_v154_addr']}` | {x['size']} | {x['name'][:110]} |")
L += ['', '## All target functions', '', '| addr | size | status | skeleton | name |', '|---|---:|---|---|---|']
for r in rows:
    L.append(f"| `{r['addr']}` | {r['size']} | {r['status']} | {'yes' if r['skeleton_match'] else 'OPEN'} | {r['name'][:120]} |")
open(R + '/DELTA.md', 'w').write('\n'.join(L) + '\n')
print(json.dumps(summary))
print(json.dumps({k: v['bytes'] for k, v in clusters.items()}))
