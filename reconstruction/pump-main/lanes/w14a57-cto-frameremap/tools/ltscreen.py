#!/usr/bin/env python3
"""ltscreen.py <m.ll> <out.jsonl> [--procs N] [--only re] : alloca lifetime-marker screen for admin_cto::execute
(experiment only). For every alloca of execute that has lifetime markers, builds variants of the post-opt module
(rx.py m.ll) and runs llc + rx metric on each:
  S0  lifetime.start moved to the top of the entry block (a `let x;` hoisted to the function head)
  E0  lifetime.end markers removed (binding kept alive to the end)
  SE  all markers removed (conservative: never coloured)
  K:<rep> member kicked out of its colour class (rep's lifetime opened/closed around the member's markers)
Each row: alloca, variant, bytes, ratio, eq_main. These edits change only StackColoring input; the code still moves
because MMO aliasing through merged slots feeds the machine scheduler."""
import sys, os, re, json, subprocess, concurrent.futures as cf
ml, outp = sys.argv[1], sys.argv[2]
procs = int(sys.argv[sys.argv.index('--procs') + 1]) if '--procs' in sys.argv else 4
only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
T = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a57-cto-frameremap')
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src = open(T + '/tools/llcx.py').read(); g = {}; exec(src[:src.index("SDK=os.path.expanduser")], g)
ORIG = g['orig_window'](); BASE = g['mask'](g['elf_fn'](os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'), g['KEEP']))
L = open(ml).read().split('\n')
d0 = next(i for i, l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l)
d1 = next(i for i in range(d0, len(L)) if L[i] == '}')
allocas = {}
for i in range(d0, d1):
    m = re.match(r'  %(\S+) = alloca \[(\d+) x i8\]', L[i])
    if m: allocas[m.group(1)] = int(m.group(2))
marks = {}
for i in range(d0, d1):
    m = re.match(r'  call void @llvm\.lifetime\.(start|end)\.p0\(i64 (\d+), ptr nonnull %(\S+)\)', L[i])
    if m and m.group(3) in allocas: marks.setdefault(m.group(3), []).append((i, m.group(1), int(m.group(2))))
first_nonalloca = next(i for i in range(d0 + 2, d1) if 'alloca' not in L[i])
def variant(a, kind, rep=None):
    lines = list(L); ms = marks[a]
    if kind == 'S0':
        for i, k, n in ms:
            if k == 'start': lines[i] = ''
        lines[first_nonalloca] = f'  call void @llvm.lifetime.start.p0(i64 {ms[0][2]}, ptr nonnull %{a})\n' + lines[first_nonalloca]
    elif kind == 'E0':
        for i, k, n in ms:
            if k == 'end': lines[i] = ''
    elif kind == 'SE':
        for i, k, n in ms: lines[i] = ''
    elif kind == 'K':
        rn = allocas[rep]
        for i, k, n in ms:
            if k == 'start': lines[i] = lines[i] + f'\n  call void @llvm.lifetime.start.p0(i64 {rn}, ptr nonnull %{rep})'
            else: lines[i] = f'  call void @llvm.lifetime.end.p0(i64 {rn}, ptr nonnull %{rep})\n' + lines[i]
    return '\n'.join(lines)
def run(job):
    a, kind, rep = job; tag = f'{a}.{kind}' + (f'.{rep}' if rep else '')
    d = T + '/lt/' + re.sub(r'[^\w.]', '_', tag); os.makedirs(d, exist_ok=True)
    open(d + '/m.ll', 'w').write(variant(a, kind, rep))
    r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
    if r.returncode: return {'alloca': a, 'kind': kind, 'rep': rep, 'error': r.stderr[-300:]}
    c = g['elf_fn'](d + '/m.o', g['KEEP']); rr, sd = g['metric'](c, ORIG)
    res = {'alloca': a, 'kind': kind, 'rep': rep, 'bytes': len(c), 'ratio': round(rr, 5), 'slots': sd, 'eq_main': g['mask'](c) == BASE}
    if res['ratio'] > 0.657 and len(c) == 27400: open(d + '/fn.bin', 'wb').write(c)
    else: subprocess.run(['rm', '-rf', d])
    return res
jobs = []
reps = {}
if os.path.exists(os.path.dirname(os.path.abspath(ml)) + '/scmap.json'):
    for row in json.load(open(os.path.dirname(os.path.abspath(ml)) + '/scmap.json')):
        for j, n, z in row['members']: reps[n] = row['name']
for a in marks:
    if only and not re.search(only, a): continue
    for k in ('S0', 'E0', 'SE'): jobs.append((a, k, None))
    if a in reps and reps[a] in allocas: jobs.append((a, 'K', reps[a]))
print(len(jobs), 'jobs', file=sys.stderr)
with open(outp, 'a') as f, cf.ThreadPoolExecutor(procs) as ex:
    for res in ex.map(run, jobs):
        f.write(json.dumps(res) + '\n'); f.flush()
