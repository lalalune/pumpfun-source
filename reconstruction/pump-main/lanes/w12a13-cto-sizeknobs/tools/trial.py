#!/usr/bin/env python3
"""trial.py <name> <base> <work_idx> [knob ...]   build base (+knobs) admin_cto.rs variant, measure, save res JSON.

Variant source: $OUT/src/<name>.rs. Result: $OUT/res/<name>.json. .so files deleted unless KEEP=1.
"""
import json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genes, knobs

LANE = 'w12a13-cto-sizeknobs'
WT = f'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/{LANE}'
OUT = os.path.expanduser(f'~/.cache/pumpfun-reconstruction/lanes/{LANE}')
MEASURE = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh'
MAIN_RS = f'{OUT}/src/main.rs'   # frozen snapshot of main's admin_cto.rs
SITE = re.compile(r'(error!\(|require!\(|require_eq!\(|require_keys_eq!\(|msg!\(|panic!\(|unwrap\(\)|expect\()')


def sites(text):
    """(line, sorted site tokens) for each line carrying an error/log site: lines are code."""
    out = {}
    for i, line in enumerate(text.split('\n'), 1):
        found = {('error!(' if f == 'require!(' else f) for f in SITE.findall(line)}
        if found:
            out[i] = sorted(found)
    return out


def variant_text(base, names):
    main = open(MAIN_RS).read()
    s = genes.base_text(base, main) if base in genes.BASES else open(base).read()
    for n in names:
        if n in genes.G:
            s2 = genes.apply(genes.G[n], s, strict=False)
        else:
            s2 = genes.apply(knobs.K[n], s, strict=False)
        if s2 is None:
            return None, f'knob {n} does not apply'
        s = s2
    return s, None


def main():
    name, base, widx = sys.argv[1], sys.argv[2], sys.argv[3]
    names = sys.argv[4:]
    res_path = f'{OUT}/res/{name}.json'
    text, err = variant_text(base, names)
    rec = {'name': name, 'base': base, 'knobs': names, 'time': time.strftime('%H:%M:%S')}
    if text is None:
        rec.update(ok=False, error=err)
        json.dump(rec, open(res_path, 'w')); print(json.dumps(rec)); return
    main_text = open(MAIN_RS).read()
    btext = genes.base_text(base, main_text) if base in genes.BASES else open(base).read()
    if text.count('\n') != btext.count('\n') or sites(text) != sites(btext):
        # allow intended site edits only when the knob says so
        if not any(n.endswith('_sitesok') for n in names):
            rec.update(ok=False, error='line/site layout changed')
            json.dump(rec, open(res_path, 'w')); print(json.dumps(rec)); return
    open(f'{OUT}/src/{name}.rs', 'w').write(text)
    crate = f'{OUT}/var/{name}'
    subprocess.run(['rsync', '-a', '--delete', '--exclude', 'target', f'{WT}/programs/pump/', crate + '/'], check=True)
    open(f'{crate}/src/creator/admin_cto.rs', 'w').write(text)
    tout = f'{OUT}/t/{name}'
    if os.path.exists(tout):
        shutil.rmtree(tout)
    t0 = time.time()
    r = subprocess.run([MEASURE, crate, f'{OUT}/work{widx}', tout], text=True, capture_output=True)
    line = (r.stdout.strip().splitlines() or ['{}'])[-1]
    try:
        m = json.loads(line)
    except json.JSONDecodeError:
        m = {'ok': False, 'error': (r.stdout + r.stderr)[-1500:]}
    rec['secs'] = round(time.time() - t0)
    if m.get('ok'):
        c, h = m.get('admin_cto') or {}, m.get('swap_hop') or {}
        rec.update(ok=True, bytes=c.get('cand_bytes'), ratio=c.get('ratio'), slots=c.get('slots_diff'),
                   calls=c.get('calls_candidate'), hop_ratio=h.get('ratio'), hop_slots=h.get('slots_diff'),
                   hop_bytes=h.get('cand_bytes'), normalized=m['normalized'], raw=m['raw'], losses=m['losses'],
                   raw_losses_n=len(m['raw_losses']), gains=m['gains'], sha=m['sha'], out=tout)
        try:
            import frame
            rec['frame'] = frame.frame_of(f'{tout}/unstripped.so')
        except Exception as e:
            rec['frame'] = str(e)[:200]
    else:
        rec.update(ok=False, error=str(m.get('error'))[-800:])
    json.dump(rec, open(res_path, 'w'))
    print(json.dumps(rec))
    if os.environ.get('KEEP') != '1':
        for f in ('unstripped.so', 'candidate.so'):
            p = f'{tout}/{f}'
            if os.path.exists(p):
                os.remove(p)
        shutil.rmtree(f'{tout}/previous', ignore_errors=True)
    shutil.rmtree(crate, ignore_errors=True)


if __name__ == '__main__':
    main()
