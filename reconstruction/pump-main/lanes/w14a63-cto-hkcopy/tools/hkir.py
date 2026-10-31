#!/usr/bin/env python3
"""hkir.py <m.ll> <out.jsonl> [names...]: holder_key-copy IR variants on post-opt m.ll (llc only). Experiment only."""
import sys, os, re, json, subprocess, concurrent.futures as cf
ml, outp = sys.argv[1], sys.argv[2]; want = sys.argv[3:]
T = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a63-cto-hkcopy')
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src = open(T + '/tools/llcx.py').read(); g = {}; exec(src[:src.index("SDK=os.path.expanduser")], g)
ORIG = g['orig_window'](); BASE = g['mask'](g['elf_fn'](os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'), g['KEEP']))
T0 = open(ml).read()
def rep1(t, a, b):
    c = t.count(a); assert c == 1, (c, a[:150]); return t.replace(a, b)
SKCOPY = 'call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %sk, ptr noundef nonnull align 1 dereferenceable(32) %_403, i64 32, i1 false)\n'
SKSTART = '  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %sk)\n'
HKCOPY = '  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %hkc)\n  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %hkc, ptr noundef nonnull align 1 dereferenceable(32) %holder_key, i64 32, i1 false)\n'
SKEND = '  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %sk)\n'
M312 = 'call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t.i, ptr noundef nonnull dereferenceable(32) %holder_key, i64 32)'
M312S = 'call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t.i, ptr noundef nonnull dereferenceable(32) %sk, i64 32)'
def base_hkc(t, pos='after', end='sk', align=1, first=False):
    t = rep1(t, '  %sk = alloca [32 x i8], align 1\n', ('  %hkc = alloca [32 x i8], align ' + str(align) + '\n  %sk = alloca [32 x i8], align 1\n') if first else ('  %sk = alloca [32 x i8], align 1\n  %hkc = alloca [32 x i8], align ' + str(align) + '\n'))
    if pos == 'after': t = rep1(t, SKCOPY, SKCOPY + HKCOPY)
    elif pos == 'before': t = rep1(t, SKSTART, HKCOPY + SKSTART)
    if end == 'sk': t = t.replace(SKEND, SKEND + '  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %hkc)\n')
    return t
def arm(t):  # holder-arm target reads from the copy
    t = rep1(t, 'dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %hk, i64 7', 'dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %hkc, i64 7')
    for k in ('7', '8', '9'):
        n = {'7': '7', '8': '15', '9': '23'}[k]
        t = rep1(t, f'%target.i.sroa.{k}.0.holder_key.sroa_idx = getelementptr inbounds i8, ptr %holder_key, i64 {n}', f'%target.i.sroa.{k}.0.holder_key.sroa_idx = getelementptr inbounds i8, ptr %hkc, i64 {n}')
    return t
def m312(t, swap=False):
    if not swap: return rep1(t, M312, M312.replace('%holder_key', '%hkc'))
    t = rep1(t, M312, '@@B@@'); t = rep1(t, M312S, M312.replace('%holder_key', '%hkc')); return t.replace('@@B@@', M312S)
def swaponly(t):
    t = rep1(t, M312, '@@B@@'); t = rep1(t, M312S, M312); return t.replace('@@B@@', M312S)
def kick(t, a, r, rn):  # kick alloca a out of class rep r (size rn)
    L = t.split('\n'); out = []
    for l in L:
        m = re.match(r'  call void @llvm\.lifetime\.(start|end)\.p0\(i64 (\d+), ptr nonnull %(\S+)\)', l)
        if m and m.group(3) == a:
            if m.group(1) == 'start': out += [l, f'  call void @llvm.lifetime.start.p0(i64 {rn}, ptr nonnull %{r})']
            else: out += [f'  call void @llvm.lifetime.end.p0(i64 {rn}, ptr nonnull %{r})', l]
        else: out.append(l)
    return '\n'.join(out)
K12 = lambda t: kick(t, '_12.i', '_112.i', 32)
KSK = lambda t: kick(t, 'sk', 'authority_info.i', 48)
V = {}
for pos in ('after', 'before'):
    for a in (0, 1):
        for sw in (0, 1):
            for k12 in (0, 1):
                for ksk in (0, 1):
                    nm = f'h_{pos[0]}{"_arm" if a else ""}{"_sw" if sw else ""}{"_k12" if k12 else ""}{"_ksk" if ksk else ""}'
                    def f(t, pos=pos, a=a, sw=sw, k12=k12, ksk=ksk):
                        t = base_hkc(t, pos)
                        if a: t = arm(t)
                        t = m312(t, sw)
                        if k12: t = K12(t)
                        if ksk: t = KSK(t)
                        return t
                    V[nm] = f
for pos in ('after','before'):
    for sw in (0,1):
        for k12 in (0,1):
            V[f'f_{pos[0]}{"_sw" if sw else ""}{"_k12" if k12 else ""}'] = (lambda t,pos=pos,sw=sw,k12=k12: (K12 if k12 else (lambda x:x))(m312(arm(base_hkc(t,pos,first=True)),sw)))
V['ksk'] = KSK; V['ksk_k12'] = lambda t: K12(KSK(t))
V['k12'] = K12; V['swap'] = swaponly; V['swap_k12'] = lambda t: K12(swaponly(t))
V['h_a_arm_noend'] = lambda t: m312(arm(base_hkc(t, 'after', None)))
V['h_a_cmponly'] = lambda t: base_hkc(t, 'after')  # copy but unused -> sanity
def run(nm):
    d = T + '/hk/' + nm; os.makedirs(d, exist_ok=True)
    try: t = V[nm](T0)
    except AssertionError as e: return {'name': nm, 'error': str(e)[:200]}
    open(d + '/m.ll', 'w').write(t)
    r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
    if r.returncode: return {'name': nm, 'error': r.stderr[-300:]}
    c = g['elf_fn'](d + '/m.o', g['KEEP']); rr, sd = g['metric'](c, ORIG)
    res = {'name': nm, 'bytes': len(c), 'ratio': round(rr, 5), 'slots': sd, 'eq_main': g['mask'](c) == BASE}
    open(d + '/fn.bin', 'wb').write(c); os.remove(d + '/m.o')
    if os.environ.get('KEEPLL') != '1': os.remove(d + '/m.ll')
    return res
names = [n for n in V if not want or any(re.fullmatch(w, n) for w in want)]
with open(outp, 'a') as f, cf.ThreadPoolExecutor(int(os.environ.get('PROCS', '4'))) as ex:
    for res in ex.map(run, names):
        print(json.dumps(res)); f.write(json.dumps(res) + '\n'); f.flush()
