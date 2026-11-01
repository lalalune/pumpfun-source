#!/usr/bin/env python3
"""rec.py <tab.jsonl> name[:combo] ...: gather union-table rows (exact M, LCS at none/r/f/rf/rfj, skel m3, Mperm/Mhc,
climb) and print a markdown table + write t/rows.jsonl. --ledger also records one ledger row per name. Experiment only."""
import sys, os, json, subprocess
T = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(T); sys.path.insert(0, T)
WT = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a28-cto-skelunion17'
L = WT + '/reconstruction/pump-main/log_attempt.py'
a = sys.argv[1:]; ledger = '--ledger' in a; a = [x for x in a if x != '--ledger']
tabf = a[0]; items = a[1:]
TAB = {}
for l in open(tabf):
    x = json.loads(l)
    if x['name'] in TAB:
        TAB[x['name']]['lcs'].update(x['lcs']); TAB[x['name']]['reg'].update(x['reg'])
    else:
        TAB[x['name']] = x
import skel, d as D
def m3(path):
    b = D.load(path); return skel.M(b, 3)
rows = []
for it in items:
    n, _, combo = it.partition(':')
    x = TAB[n]; st = {}; sn = n[:-2] if n.endswith('mv') else n
    p = f'{OUT}/st/{sn}/step.json'
    if os.path.exists(p):
        st = json.load(open(p))
    fn = f'{OUT}/st/{sn}/fn.bin' if os.path.exists(f'{OUT}/st/{sn}/fn.bin') else f'{OUT}/fx/{sn}/fn.bin'
    r = {'name': n, 'combo': combo or n, 'M': x['M'], 'bytes': x['bytes'], 'lcs': x['lcs'], 'm3': m3(fn),
         'Mperm': st.get('Mperm'), 'Mhc': st.get('Mhc'), 'mv58': st.get('mv58'),
         'climb': (st.get('climb') or {}).get('M'), 'climb_bytes': (st.get('climb') or {}).get('bytes'),
         'climb_forces': (st.get('climb') or {}).get('forces'), 'climb_rounds': st.get('climb_rounds'), 'reg': x['reg'],
         'climb2': st.get('climb2'), 'climb2_at': st.get('climb2_at'), 'joint': st.get('joint')}
    rows.append(r)
base = rows[0]
print('| step | M @ bytes | LCS none | r | f | rf | rfj | rfj-none | m3 | Mperm / Mhc | climb (1 pass) | re-vote climb (forces) | at 27,400 | joint Mhc |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |')
for r in rows:
    lc = r['lcs']
    cl = '%s @%s (%d forces)' % (r['climb'], r['climb_bytes'], len(r['climb_forces'] or [])) if r['climb'] else '-'
    c2 = r['climb2'] or {}; jt = r['joint'] or {}
    print('| %s | %d @%d | %d | %d | %d | %d | %d | %d | %d | %s / %s | %s | %s | %s | %s |' % (
        r['combo'] + (' +MV58' if r['mv58'] else ''), r['M'], r['bytes'], lc['none'], lc['r'], lc['f'], lc['rf'], lc['rfj'],
        lc['rfj'] - lc['none'], r['m3'], r['Mperm'], r['Mhc'], cl,
        ('%s @%s (%s)' % (c2.get('M'), c2.get('bytes'), c2.get('n'))) if c2 else '-', r['climb2_at'] or '-', jt.get('Mhc', '-')))
with open(f'{OUT}/t/rows.jsonl', 'a') as f:
    for r in rows:
        f.write(json.dumps(r) + '\n')
if ledger:
    for r in rows:
        key = '0x22a10-w17-53ec7fb-skelunion17-%s-v1' % r['name']
        c = subprocess.run(['python3', L, 'check', '--dedupe-key', key], capture_output=True, text=True)
        if '"duplicate": true' in c.stdout:
            continue
        lc = r['lcs']
        note = ('slim pre-opt oracle on main 53ec7fb53 (M 2295, LCS none/r/f/rf/rfj 2300/2631/2503/2888/3000, m3 2804, Mperm/Mhc 2321/2329, climb 2316@27392). '
                'this: M %d @%d B, LCS %d/%d/%d/%d/%d, m3 %d, Mperm/Mhc %s/%s, climb %s @%s forces %s%s' % (
                    r['M'], r['bytes'], lc['none'], lc['r'], lc['f'], lc['rf'], lc['rfj'], r['m3'], r['Mperm'], r['Mhc'],
                    r['climb'], r['climb_bytes'], r['climb_forces'], ' (+MV58 post-opt)' if r['mv58'] else '')) + ('; re-vote climb %s @%s (%s forces), at 27400 %s; joint Mhc %s' % ((r['climb2'] or {}).get('M'), (r['climb2'] or {}).get('bytes'), (r['climb2'] or {}).get('n'), r['climb2_at'], (r['joint'] or {}).get('Mhc')) if r['climb2'] else '')
        data = {'output': f'{OUT}/st/{r["name"]}', 'normalized': None, 'raw': None, 'losses': [], 'raw_losses': [],
                'target': {'ratio': round(2 * r['M'] / (3339 + r['bytes'] // 8), 5), 'slots_diff': None, 'cand_bytes': r['bytes']},
                'notes': note}
        st = 'analyzed' if r['name'] == 'm0' else ('rejected' if r['M'] <= 2295 else 'analyzed')
        subprocess.run(['python3', L, 'record', '--lane', 'w17a28-cto-skelunion17', '--approach', 'skelunion17', '--target', '0x22a10',
                        '--dedupe-key', key, '--hypothesis', 'union step %s on main 53ec7fb53 (genes: %s): skeleton vs naming' % (r['name'], r['combo']),
                        '--status', st, '--data', json.dumps(data)], capture_output=True, text=True)
        print('recorded', key, st)
