#!/usr/bin/env python3
"""mk.py <name>...: build ed/<name>.ll from rx/m0/m.ll (main 90300f9 post-opt IR) with the named IR edit (llc-only oracle).
The original %170 / %cashback stay in place (dead) so unnamed value numbering is kept."""
import sys, os
O = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(O + '/rx/m0/m.ll').read()

def rep(t, a, b, cnt=1):
    c = t.count(a)
    assert c == cnt, (c, a[:100])
    return t.replace(a, b)

FS = '  %_11.i285 = alloca [0 x i8], align 1\n'
CB = '  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n'
Z = '  %170 = zext i1 %cashback.sroa.0.0.off0 to i8\n'
ST = '  store i8 %170, ptr %584, align 1\n'
STZ = '  store i8 %cbz, ptr %584, align 1\n'
NH = '  %cbh = and i8 %0, -3\n  %cbn = icmp eq i8 %cbh, 0\n'

def E(name, t):
    if name == 'm0':
        return t
    if name == 'rc':  # recompute !holder&&cb at the curve store from the arg and the entry load
        return rep(t, ST, NH + '  %cbx = and i1 %cbn, %extract.t\n  %cbz = zext i1 %cbx to i8\n' + STZ)
    if name == 'rcl':  # recompute from the arg and a reload of the curve byte (state re-derived)
        return rep(t, ST, '  %cbl = load i8, ptr %584, align 1\n  %cbe = icmp ne i8 %cbl, 0\n' + NH +
                   '  %cbx = and i1 %cbn, %cbe\n  %cbz = zext i1 %cbx to i8\n' + STZ)
    if name == 'rclz':  # select form: holder?0:byte
        return rep(t, ST, '  %cbl = load i8, ptr %584, align 1\n' + NH + '  %cbz = select i1 %cbn, i8 %cbl, i8 0\n' + STZ)
    if name == 'rch':  # !holder recomputed from the arg, st.cashback i1 kept from the head
        return rep(t, ST, NH + '  %cbx = and i1 %extract.t, %cbn\n  %cbz = zext i1 %cbx to i8\n' + STZ)
    if name in ('sj', 'sj8'):  # cashback stored to a stack slot at the validate-exit join, reloaded at the curve store
        ty = 'i64' if name == 'sj8' else 'i8'
        t = rep(t, FS, FS + f'  %cbslot = alloca {ty}, align 8\n')
        if ty == 'i8':
            t = rep(t, Z, Z + '  store i8 %170, ptr %cbslot, align 1\n')
            t = rep(t, ST, '  %cbz = load i8, ptr %cbslot, align 1\n' + STZ)
        else:
            t = rep(t, Z, Z + '  %cb64 = zext i8 %170 to i64\n  store i64 %cb64, ptr %cbslot, align 8\n')
            t = rep(t, ST, '  %cbld64 = load i64, ptr %cbslot, align 8\n  %cbz = trunc i64 %cbld64 to i8\n' + STZ)
        return t
    raise SystemExit('unknown ' + name)

for n in sys.argv[1:]:
    open(f'{O}/ed/{n}.ll', 'w').write(E(n, src))
    print(n)
