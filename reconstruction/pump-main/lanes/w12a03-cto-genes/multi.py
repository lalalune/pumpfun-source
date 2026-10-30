#!/usr/bin/env python3
"""Multi-copy gene screen: one build carries many gene variants of admin_cto::execute.

  multi.py <tag> <work_index> <trial> [<trial> ...]     trial = name=gene1+gene2+...

Each variant becomes its own module file src/creator/admin_cNN.rs (same path length as admin_cto.rs, so
file!() strings keep their length) holding the variant's validate/execute/wallet/sweep/token helpers at
exactly the same line numbers as admin_cto.rs (the Accounts struct and the event lines are blanked and
imported from crate::admin_cto). The anchor handler dispatches to each copy on an
opaque `ctx.remaining_accounts.len()` value (one direct call per copy, like the real execute). The real admin_cto::execute is
untouched. After the build, target_metric.py and frame.py measure every copy against the original window
0x22a10. A gene-free copy (`main=`) is the fidelity control: it must reproduce main's 0.43919 / 27,400 B.
Screening only: everything that looks good is confirmed with a real measure.sh build.
"""
import json, os, re, shutil, subprocess, sys, time, importlib.util
from pathlib import Path

LANE = 'w12a03-cto-genes'
SWARM = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm')
WT = SWARM / 'worktrees' / LANE
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes' / LANE
H = SWARM / 'worktrees/w11-baseline/reconstruction/harness'
REL = 'src/creator/admin_cto.rs'
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('genes', str(HERE / 'genes.py'))
genes = importlib.util.module_from_spec(spec); spec.loader.exec_module(genes)
KEEP = ("#[used] static KEEP_EXECUTE: for<'a,'b,'c,'info> fn(Context<'a,'b,'c,'info,AdminCto<'info>>,Option<bool>,Option<u64>,Option<Pubkey>)->Result<()> = execute;\n")


def copy_text(text):
    lines = text.split('\n')
    assert lines[7] == '', repr(lines[7])
    lines[7] = 'use crate::{AdminCto,AdminCtoEvent};'
    assert lines[8] == '#[derive(Accounts)]', lines[8]
    assert 'struct CtoState{' in lines[99], lines[99][:40]
    for i in range(8, 99):
        lines[i] = ''
    return '\n'.join(lines).rstrip('\n') + '\n'


def main():
    tag, widx, trials = sys.argv[1], sys.argv[2], sys.argv[3:]
    base = Path(os.environ.get('MULTI_BASE', str(WT / 'programs/pump' / REL))).read_text()
    import hashlib
    btag = os.environ.get('MULTI_BASE_TAG') or hashlib.sha256(base.encode()).hexdigest()[:10]
    var = OUT / 'var' / f'multi_{tag}'
    if var.exists():
        shutil.rmtree(var)
    var.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['rsync', '-a', '--exclude', 'target', f'{WT}/programs/pump/', f'{var}/'], check=True)
    lib = (var / 'src/lib.rs').read_text()
    mods = []
    plan = []
    for i, t in enumerate(trials, 1):
        name, _, gs = t.partition('=')
        gl = [g for g in gs.split('+') if g]
        try:
            text = genes.apply(base, gl)
        except Exception as e:
            print(json.dumps({'name': name, 'status': 'apply-failed', 'error': str(e)[:200]}), flush=True)
            continue
        m = f'admin_c{i:02d}'
        (var / f'src/creator/{m}.rs').write_text(copy_text(text))
        mods.append(f'#[path="creator/{m}.rs"]pub mod {m};')
        plan.append((name, gl, m))
    call = '{admin_cto::execute(ctx,is_holder_reward,creator_fee_bps,new_creator)}'
    assert lib.count(call) == 1
    arms = ''.join(f'{100 + int(m[-2:])}=>{m}::execute(ctx,is_holder_reward,creator_fee_bps,new_creator),' for _, _, m in plan)
    lib = lib.replace(call, '{match ctx.remaining_accounts.len(){' + arms + '_=>admin_cto::execute(ctx,is_holder_reward,creator_fee_bps,new_creator)}}')
    (var / 'src/lib.rs').write_text(lib.rstrip('\n') + '\n' + ''.join(mods) + '\n')
    tout = OUT / 't' / f'multi_{tag}'
    tout.mkdir(parents=True, exist_ok=True)
    work = OUT / f'work{widx}'
    t0 = time.time()
    env = dict(os.environ, PUMP_BUILD_SLOTS=os.environ.get('PUMP_BUILD_SLOTS', '10'))
    r = subprocess.run(['python3', str(H / 'fastbuild.py'), '--src', str(var), '--work', str(work), '--out', str(tout)], capture_output=True, text=True, env=env)
    secs = int(time.time() - t0)
    try:
        b = json.loads(r.stdout)
    except Exception:
        b = {'ok': False, 'raw': r.stdout[-500:]}
    so = tout / 'unstripped.so'
    stack = b.get('stack_warnings') or []
    if not b.get('ok'):
        built = work / 'target/sbpf-solana-solana/release/pump_recovered.so'
        if stack and built.exists():
            shutil.copy2(built, so)
        else:
            print(json.dumps({'tag': tag, 'status': 'build-failed', 'secs': secs, 'err': (r.stderr[-1500:] + json.dumps(b)[-500:])}), flush=True)
            return
    res = []
    for name, gl, m in plan + [('real_admin_cto', [], 'admin_cto')]:
        tm = subprocess.run(['python3', str(H / 'target_metric.py'), str(so), '0x22a10', '--sym', f'{m}::execute$', '--slots', '4000'], capture_output=True, text=True)
        try:
            d = json.loads(tm.stdout.strip().splitlines()[0])
        except Exception:
            d = {}
        fr = subprocess.run(['python3', str(HERE / 'frame.py'), str(so), '--sym', f'{m}::execute$'], capture_output=True, text=True)
        try:
            f = json.loads(fr.stdout.strip().splitlines()[-1])
        except Exception:
            f = {}
        row = {'tag': tag, 'base': btag, 'name': name, 'genes': gl, 'module': m, 'bytes': d.get('cand_bytes'), 'ratio': d.get('ratio'), 'slots': d.get('slots_diff'),
               'calls': d.get('calls_candidate'), 'frame_first': f.get('first_store_dec'), 'frame_common': f.get('common_with_orig'),
               'stack_warn': any(m in s for s in stack), 'secs': secs}
        if row['bytes'] is not None:
            row['d_bytes'] = row['bytes'] - 27400
            row['d_ratio'] = round(row['ratio'] - float(os.environ.get('MULTI_BASE_RATIO', '0.43919')), 5)
        res.append(row)
        print(json.dumps(row), flush=True)
    with (OUT / 'multi.jsonl').open('a') as fh:
        for row in res:
            fh.write(json.dumps(row) + '\n')
    for p in ('unstripped.so', 'candidate.so'):
        (tout / p).unlink(missing_ok=True)
    shutil.rmtree(var, ignore_errors=True)


if __name__ == '__main__':
    main()
