#!/usr/bin/env python3
"""Write the admin_cto gene table from run/qd results and multi-copy screens.

  table.py <results.jsonl> <genes-cto.json> [<GENES.md>] [--multi <multi.jsonl>]

Every gene in genes.py gets a row. `build` columns come from real measure.sh builds of the gene alone on
main (results.jsonl); `screen` columns come from multi-copy screening builds (multi.py), where the gene's
execute is one of several copies compiled in one crate (fidelity checked by the gene-free control copy).
Deltas are against main 20a1ae9c0 (admin_cto 0.43919 at 27,400 B, 3,352 slots). Composites are listed
separately.
"""
import json, sys, time, importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('genes', str(Path(__file__).resolve().parent / 'genes.py'))
genes = importlib.util.module_from_spec(spec); spec.loader.exec_module(genes)
args = sys.argv[1:]
multi = None
if '--multi' in args:
    i = args.index('--multi'); multi = args[i + 1]; del args[i:i + 2]
rows = {}
for l in Path(args[0]).read_text().splitlines():
    if l.strip():
        r = json.loads(l)
        rows[r['name']] = r
screens = {}
if multi and Path(multi).exists():
    for l in Path(multi).read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get('bytes') is not None and r['name'] not in ('real_admin_cto',):
                screens[r['name']] = r
base = open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a03-cto-genes/programs/pump/src/creator/admin_cto.rs').read()
import difflib
single, comp = [], []
for name in genes.G:
    r = rows.get(name) if (rows.get(name) or {}).get('genes') == [name] else None
    s = screens.get(name) if (screens.get(name) or {}).get('genes') == [name] else None
    text = genes.apply(base, [name])
    e = {'gene': name, 'source': genes.SRC.get(name, '?'),
         'diff': ''.join(difflib.unified_diff(base.splitlines(True), text.splitlines(True), 'main/admin_cto.rs', f'{name}/admin_cto.rs', n=0))}
    if r:
        e.update({'build_status': r.get('status'), 'bytes': r.get('bytes'), 'd_bytes': r.get('d_bytes'), 'ratio': r.get('ratio'), 'd_ratio': r.get('d_ratio'),
                  'slots': r.get('slots'), 'normalized': r.get('normalized'), 'raw': r.get('raw'), 'raw_losses_n': r.get('raw_losses_n'),
                  'frame_first': r.get('frame_first'), 'sha': r.get('sha'), 'imported_from': r.get('imported_from'), 'error': r.get('error')})
    if s:
        e.update({'screen_bytes': s.get('bytes'), 'screen_d_bytes': s.get('d_bytes'), 'screen_ratio': s.get('ratio'), 'screen_d_ratio': s.get('d_ratio'),
                  'screen_calls': s.get('calls'), 'screen_frame_first': s.get('frame_first'), 'screen_tag': s.get('tag'), 'screen_stack_warn': s.get('stack_warn')})
    if not r and not s:
        e['build_status'] = 'not measured'
    single.append(e)
for name, r in rows.items():
    if (r.get('genes') or []) == [name]:
        continue
    comp.append({k: r.get(k) for k in ('name', 'genes', 'status', 'bytes', 'd_bytes', 'ratio', 'd_ratio', 'slots', 'normalized', 'raw',
                                       'raw_losses_n', 'sha', 'imported_from', 'frame_first')} | {'kind': 'build'})
for name, s in screens.items():
    if len(s.get('genes') or []) > 1:
        comp.append({'name': name, 'genes': s['genes'], 'bytes': s.get('bytes'), 'd_bytes': s.get('d_bytes'), 'ratio': s.get('ratio'),
                     'd_ratio': s.get('d_ratio'), 'frame_first': s.get('frame_first'), 'kind': f"screen {s.get('tag')}"})


def dr(e):
    v = e.get('d_ratio') if e.get('d_ratio') is not None else e.get('screen_d_ratio')
    return v if v is not None else -9


single.sort(key=lambda e: (e.get('build_status') == 'not measured', -dr(e)))
comp.sort(key=lambda e: (e.get('bytes') != 27400, -(e.get('ratio') or 0)))
doc = {
    'lane': 'w12a03-cto-genes', 'target': '0x22a10 admin_cto::execute', 'updated_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'base': {'main': '20a1ae9c0 (programs/ identical through 241542515)', 'ratio': 0.43919, 'bytes': 27400, 'slots_diff': 3352, 'frame_first_store': -2288,
             'orig_frame_first_store': -2344},
    'gene_script': 'reconstruction/pump-main/lanes/w12a03-cto-genes/genes.py on branch swarm/w12a03-cto-genes: apply(text, [names]) on main admin_cto.rs',
    'columns': {'d_bytes/d_ratio': 'real measure.sh build of the gene alone on main', 'screen_*': 'multi-copy screen (multi.py), same gene alone',
                'frame_first': 'first [r10+off] store of execute (orig -2344, main -2288)'},
    'notes': 'A size change costs 686 raw windows, so only 27,400 B composites are landable. Gene effects are not additive '
             '(e.g. wallet_flags -88 B alone, k4 = wallet_flags+region2_tree+fee_unwrap+canedit_first+old_fee_first is -16 B).',
    'genes': single, 'composites': comp,
}
Path(args[1]).write_text(json.dumps(doc, indent=1) + '\n')
if len(args) > 2:
    f = lambda v: '-' if v is None else v
    out = ['| gene | source | build d_bytes | build d_ratio | screen d_bytes | screen d_ratio | frame | status |',
           '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for e in single:
        out.append(f"| `{e['gene']}` | {e['source']} | {f(e.get('d_bytes'))} | {f(e.get('d_ratio'))} | {f(e.get('screen_d_bytes'))} | "
                   f"{f(e.get('screen_d_ratio'))} | {f(e.get('frame_first') or e.get('screen_frame_first'))} | {e.get('build_status') or 'screened'} |")
    out += ['', '| composite | genes | bytes | ratio | kind |', '| --- | --- | ---: | ---: | --- |']
    for e in comp:
        out.append(f"| `{e['name']}` | {' + '.join(e.get('genes') or []) or 'main'} | {f(e.get('bytes'))} | {f(e.get('ratio'))} | {e.get('kind')} |")
    Path(args[2]).write_text('\n'.join(out) + '\n')
print(len(single), 'genes,', len(comp), 'composites,', sum(1 for e in single if e.get('build_status') != 'not measured'), 'measured')
