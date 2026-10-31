# irprobe_fill.py [names]: post-opt IR probes of validate fill placement (experiment only).
# Base B: V_d_maxf post-opt m.ll with the line-338 OK-block store value replaced by f-1 (%160): 27,392 B / M 2,248.
# Each probe is a list of exact (old, new) text edits on B, run through tools/pv.py (stock llc + M).
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
T = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay'
B = T + '/pv/st_160/m.ll'
OKH = 'bb65.i:                                           ; preds = %bb58.i\n'
OK_OLD = OKH + '  store i64 %160, ptr %37, align 8, !alias.scope !8547, !noalias !8599\n  br label %bb75'
def ok(*lines): return OKH + ''.join('  ' + l + '\n' for l in lines) + '  br label %bb75'
CHH = 'bb58.i:                                           ; preds = %bb54.i\n'
CHK_OLD = CHH + '  %160 = add i64 %2, -1'
def chk(*lines): return CHH + ''.join('  ' + l + '\n' for l in lines) + '  %160 = add i64 %2, -1'
B54_OLD = '  %_112.not.i = icmp eq i8 %26, 0\n  br i1 %_112.not.i, label %bb59.i, label %bb58.i'
def b54(*lines): return ''.join('  ' + l + '\n' for l in lines) + B54_OLD
SA = '!alias.scope !8547, !noalias !8599'
F = f'store i64 %2, ptr %37, align 8, {SA}'          # st.max_fee = f   (%2 = fee payload, %37 = st+32)
M1 = f'store i64 %160, ptr %37, align 8, {SA}'       # st.max_fee = f-1
FC0 = f'store i8 0, ptr %44, align 1, {SA}'          # st.fee_configurable = false (st+45)
P = {
    'P0_base': [],
    'P1_fpre_fc0': [(CHK_OLD, chk(F)), (OK_OLD, ok(FC0))],
    'P2_take334_m1': [(B54_OLD, b54(FC0))],
    'P3_two_m1_fc0': [(OK_OLD, ok(M1, FC0))],
    'P4_two_0_fc0': [(OK_OLD, ok(f'store i64 0, ptr %37, align 8, {SA}', FC0))],
    'P5_take334_f': [(B54_OLD, b54(FC0)), (OK_OLD, ok(F))],
    'P6_fc0': [(OK_OLD, ok(FC0))],
    'P7_fpre_only': [(CHK_OLD, chk(F)), (OK_OLD, ok())],
    'P8_fpre_m1': [(CHK_OLD, chk(F))],
    'P9_take334_fc0': [(B54_OLD, b54(FC0)), (OK_OLD, ok(FC0))],
    'P10_may334_m1': [(B54_OLD, b54(f'store i8 0, ptr %38, align 8, {SA}'))],
    'Q1_f54_fc0': [(B54_OLD, b54(F)), (OK_OLD, ok(FC0))],
    'Q2_f54_m1': [(B54_OLD, b54(F))],
    'Q3_fpost_fc0': [(CHK_OLD, CHK_OLD + '\n  ' + F), (OK_OLD, ok(FC0))],
    'Q4_fpre_ql1': [(CHK_OLD, chk(F)), (OK_OLD, ok(f'store i8 1, ptr %41, align 1, {SA}'))],
    'Q5_fpre_may0': [(CHK_OLD, chk(F)), (OK_OLD, ok(f'store i8 0, ptr %38, align 1, {SA}'))],
    'Q6_fpre_max0': [(CHK_OLD, chk(F)), (OK_OLD, ok(f'store i64 0, ptr %37, align 8, {SA}'))],
    'Q7_f54_fc1': [(B54_OLD, b54(F)), (OK_OLD, ok(f'store i8 1, ptr %44, align 1, {SA}'))],
}
def run(n):
    args = ['python3', T + '/tools/pv.py', B, 'fill_' + n]
    for o, w in (P[n] or [('br label %bb75\n\nbb75:', 'br label %bb75\n\nbb75:')]): args += [o, w]
    r = subprocess.run(args, capture_output=True, text=True)
    return n, (r.stdout.strip() or r.stderr.strip()[-300:])
if __name__ == '__main__':
    sel = sys.argv[1:] or list(P)
    with ThreadPoolExecutor(4) as ex:
        for n, o in ex.map(run, sel): print(n, o, flush=True)
