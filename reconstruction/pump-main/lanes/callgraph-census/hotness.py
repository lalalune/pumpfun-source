#!/usr/bin/env python3
"""Per-site hot/cold map for the 16 unmatched windows (diagnostic).

  hotness.py --remarks <build.log from capture_inline.py --lines> [--census CENSUS.json] [--md HOTNESS.md]

Ours: every inliner remark into the target function for ToString::to_string (cost 130) or
AccountInfo::clone (cost 60), keyed by source line, with the threshold LLVM used: 45 = cold call
site (block frequency < 2 % of entry, no profile), 250/325/375 = normal. Original: error-message form per
following Source line from CENSUS.json (`fmt` = to_string inlined = hot, `to_string` = cold).
"""
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from win import demangle  # noqa: E402

FN = {'0x14f4e0': r'pump_recovered::pump_recovered::buy_exact_sol_in$', '0x80df8': r'trade::v3_buy_costs$',
      '0x6cd78': r'process_cashback_inner$', '0x83c00': r'trade::v3_execute_buy$', '0x13f630': r'buy_exact_quote_in_handler$',
      '0x13b9b8': r'buy_v2::buy_handler$', '0x144508': r'sell_v2::execute$', '0x4c158': r'create_token_account_v2$',
      '0x147ba0': r'^pump_recovered::trade::buy$', '0x14a8a8': r'^pump_recovered::trade::sell$',
      '0x1489f8': r'^pump_recovered::trade::buy_exact_quote$', '0x72810': r'sweep::execute$', '0x1e7c0': r'create_v2::execute$',
      '0x77940': r'cashback::claim_v2$', '0x5b3b0': r'multi_hop_curve::swap_hop$', '0x22a10': r'admin_cto::execute$'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--remarks', type=Path, required=True)
    ap.add_argument('--census', type=Path, default=Path(__file__).with_name('CENSUS.json'))
    ap.add_argument('--md', type=Path); ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    ours = defaultdict(list)
    for l in a.remarks.read_text(errors='replace').splitlines():
        m = re.match(r"note: (\S+) inline \((\w+)\): '([^']+)'[^']*'([^']+)'", l)
        if not m:
            continue
        loc, kind, callee, caller = m.group(1), m.group(2), demangle(m.group(3)), demangle(m.group(4))
        kindc = 'to_string' if 'ToString>::to_string' in callee else 'clone' if 'AccountInfo as core::clone::Clone' in callee else None
        if not kindc:
            continue
        thr = re.search(r'threshold=(\d+)', l)
        for w, rx in FN.items():
            if re.search(rx, caller):
                ours[w].append({'loc': loc.split('src/')[-1], 'callee': kindc, 'inlined': kind == 'success',
                                'threshold': int(thr.group(1)) if thr else None, 'hot': bool(thr and int(thr.group(1)) > 45)})
    census = {t['original']: t for t in json.loads(a.census.read_text())['targets']}
    out, md = {}, ['# Per-site hot/cold map', '',
                   'hot = call site at >= 2 % of entry block frequency (LLVM inlines the cost-60 clone / cost-130 to_string there); cold = below (threshold 45, stays a call).',
                   'Ours from `-C remark=inline -C debuginfo=line-tables-only` (experiment only). Original from CENSUS error-message form by following Source line.', '']
    for w in FN:
        o = census.get(w, {}).get('error_format_forms', {}).get('orig', [])
        out[w] = {'ours': ours.get(w, []), 'orig_error_sites': o}
        md.append(f"## {w} {census.get(w, {}).get('candidate', '')}\n")
        ol = ', '.join(f"{x['line']} {'hot' if x['form'] == 'fmt' else 'cold'}" for x in o) or '-'
        md.append(f"- original error sites (by following Source line): {ol}")
        seen = []
        for r in ours.get(w, []):
            k = (r['loc'], r['callee'], r['hot'])
            if k not in seen:
                seen.append(k)
        md.append('- ours: ' + (', '.join(f"{l} {c} {'hot' if h else 'cold'}" for l, c, h in seen) or '-'))
        md.append('')
    if a.json:
        a.json.write_text(json.dumps(out, indent=1) + '\n')
    if a.md:
        a.md.write_text('\n'.join(md) + '\n')
    print(json.dumps({w: len(v['ours']) for w, v in out.items()}))


if __name__ == '__main__':
    main()
