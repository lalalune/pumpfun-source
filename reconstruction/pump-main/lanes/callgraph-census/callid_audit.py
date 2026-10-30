#!/usr/bin/env python3
"""Hidden call-target audit: normalized matches whose call targets are the wrong function.

  callid_audit.py [--cand unstripped.so] [--json out.json]

score.py masks direct-call immediates, so a window can match normalized while calling a different
function than the original (e.g. Account::try_from vs try_from_unchecked: identical bodies after
masking, differing only in which deserializer they call). Such windows can never match raw.

Method (greatest-fixpoint bisimulation over the call graph):
  R(o, c) starts as "same length and same normalized body" (score.py's relation); the 16 unmatched
  windows are pinned to their README candidate. Repeatedly drop (o, c) when some call site i of o
  calls t_o and the same site of c calls t_c with (t_o, t_c) not in R. At the fixpoint, a window
  that matched normalized but has no surviving candidate calls a wrong target somewhere; we report
  the first failing site per candidate (its callee pair), and the "root" sites whose callee pairs
  fail on body hash (level 0) rather than only through their own callees.
For the pinned unmatched windows, the census difflib alignment of call sequences is checked the same
way (sites aligned by census whose targets are normalized-equal but not bisimilar).
Diagnostic only; score.py decides acceptance.
"""
import argparse, hashlib, json, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import census as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', type=Path, required=True)
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    wins = C.original_windows()
    O = C.Image(C.ORIG_PATH, {w['start']: (w['bytes'], []) for w in wins})
    cf = {}
    for s, n, nm in C.candidate_functions(a.cand):
        cf.setdefault(s, (n, []))[1].append(nm)
    K = C.Image(a.cand, cf)

    def nh(img, s):
        return (img.funcs[s][0], hashlib.sha256(C.normalize(img.raw(s), s, img.secs)).digest())
    by = defaultdict(set)
    for s in cf:
        by[nh(K, s)].add(s)
    R = {o: set(by.get(nh(O, o), ())) for o in O.funcs}
    matched = {o for o in R if R[o]}
    pinned = {}
    for o, rx in C.PAIRS.items():
        import re
        cs = [s for s, (n, nms) in cf.items() if any(re.search(rx, C.demangle(x)) for x in nms)]
        pinned[o] = max(cs, key=lambda c: C.ratio(O, o, K, c))
        R[o] = {pinned[o]}
    ocalls = {o: [t for _, t in O.calls(o) if not isinstance(t, tuple)] for o in O.funcs}
    ccalls = {}

    def cc(c):
        if c not in ccalls:
            ccalls[c] = [t for _, t in K.calls(c) if not isinstance(t, tuple)]
        return ccalls[c]

    def ok_pair(to, tc):
        if to not in R:  # call into something that is not a window (should not happen)
            return True
        return tc in R[to]

    changed = True
    rounds = 0
    while changed:
        changed = False; rounds += 1
        for o in list(R):
            if o in pinned:
                continue
            keep = set()
            for c in R[o]:
                a_, b_ = ocalls[o], cc(c)
                if len(a_) == len(b_) and all(ok_pair(x, y) for x, y in zip(a_, b_)):
                    keep.add(c)
            if keep != R[o]:
                R[o] = keep; changed = True

    def cname(c):
        return C.short(cf[c][1][0]) if c in cf else hex(c)

    def body_eq(to, tc):
        return to in O.funcs and tc in cf and nh(O, to) == nh(K, tc)

    hidden = []
    for o in sorted(matched - set(pinned)):
        if R[o]:
            continue
        cands = sorted(by.get(nh(O, o), ()))
        rows = []
        for c in cands:
            bad = [(i, x, y) for i, (x, y) in enumerate(zip(ocalls[o], cc(c))) if not ok_pair(x, y)]
            rows.append({'cand': hex(c), 'name': cname(c), 'bad_sites': [
                {'i': i, 'orig_callee': hex(x), 'orig_callee_ok_names': sorted({cname(z) for z in by.get(nh(O, x), ())})[:3] if x in O.funcs else [],
                 'our_callee': hex(y), 'our_name': cname(y), 'body_equal': body_eq(x, y)} for i, x, y in bad[:6]]})
        hidden.append({'window': hex(o), 'bytes': O.funcs[o][0], 'candidates': rows})
    # pinned targets: census-style alignment of callee sequences, sites with body-equal but not bisimilar callees
    pin_rows = []
    import difflib
    for o, c in sorted(pinned.items()):
        a_, b_ = ocalls[o], cc(c)
        ka = [hashlib.sha256(nh(O, x)[1]).hexdigest()[:12] if x in O.funcs else '?' for x in a_]
        kb = [hashlib.sha256(nh(K, y)[1]).hexdigest()[:12] if y in cf else '?' for y in b_]
        sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False)
        bad = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                continue
            for i, j in zip(range(i1, i2), range(j1, j2)):
                if not ok_pair(a_[i], b_[j]):
                    bad.append({'orig_pos': i, 'our_pos': j, 'orig_callee': hex(a_[i]), 'our_callee': hex(b_[j]), 'our_name': cname(b_[j]),
                                'bisimilar_candidates': sorted(cname(z) for z in R.get(a_[i], ()))[:4]})
        pin_rows.append({'window': hex(o), 'cand': hex(c), 'name': cname(c), 'aligned_body_equal_but_wrong_callee': bad})
    res = {'candidate': str(a.cand), 'rounds': rounds, 'normalized_matched': len(matched - set(pinned)),
           'bisimilar_matched': len([o for o in matched - set(pinned) if R[o]]), 'hidden_call_target_mismatch': hidden,
           'pinned_targets': pin_rows}
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: res[k] for k in ('rounds', 'normalized_matched', 'bisimilar_matched')}))
    for h in hidden:
        print('HIDDEN', h['window'], h['bytes'], [(r['name'], [(b['our_name'], b['orig_callee_ok_names'], b['body_equal']) for b in r['bad_sites'][:2]]) for r in h['candidates'][:2]])
    for p in pin_rows:
        if p['aligned_body_equal_but_wrong_callee']:
            print('PINNED', p['window'], p['name'], [(b['our_pos'], b['our_name'], b['bisimilar_candidates']) for b in p['aligned_body_equal_but_wrong_callee']])


if __name__ == '__main__':
    main()
