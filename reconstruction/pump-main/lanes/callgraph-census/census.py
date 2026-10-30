#!/usr/bin/env python3
"""Call-graph / inlining-boundary census for the 16 unmatched main-Pump windows.

  census.py [--cand unstripped.so] [--json CENSUS.json] [--md CENSUS-TABLES.md] [--only 0xSTART,...]

Read-only evidence. For each unmatched original window and its paired candidate function:
  * direct internal calls (op 0x85, src=1) in physical order, target = pc + 8 + imm*8;
  * every callee resolved to an identity key by normalized-body equality (score.py masking):
    original callee windows that match normalized share the key of the candidate symbol(s);
    unmatched windows are paired explicitly (PAIRS) and share a 'T:<orig>' key;
  * sequence alignment (difflib) of callee keys -> missing / extra / reordered callees;
  * inline/outline classification of every differing callee, with depth-2 evidence;
  * argument setup (writes to r1..r5 since the previous call, normalized text) per aligned call.
Only score.py decides acceptance; this is diagnostic.
"""
import argparse, difflib, hashlib, json, re, struct, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

H = Path(__file__).resolve().parents[3] / 'harness'
sys.path.insert(0, str(H))
from score import sections, normalize, body, candidate_functions, original_windows, BASE  # noqa: E402
from win import demangle, insns, objdump_text  # noqa: E402
from coords import sites as source_sites  # noqa: E402

DEFAULT_CAND = BASE / 'current/unstripped.so'

# original window -> regex for the paired candidate function (README table), best ratio wins
PAIRS = {
    0x14f4e0: r'pump_recovered::pump_recovered::buy_exact_sol_in$',
    0x80df8: r'trade::v3_buy_costs$',
    0x6cd78: r'legacy_sell::process_cashback_inner$',
    0x83c00: r'trade::v3_execute_buy$',
    0x13f630: r'buy_v2::buy_exact_quote_in_handler$',
    0x13b9b8: r'buy_v2::buy_handler$',
    0x144508: r'sell_v2::execute$',
    0x4c158: r'migrate_v2::create_token_account_v2$',
    0x147ba0: r'^pump_recovered::trade::buy$',
    0x14a8a8: r'^pump_recovered::trade::sell$',
    0x1489f8: r'^pump_recovered::trade::buy_exact_quote$',
    0x72810: r'sweep::execute$',
    0x1e7c0: r'create_v2::execute$',
    0x77940: r'cashback::claim_v2$',
    0x5b3b0: r'multi_hop_curve::swap_hop$',
    0x22a10: r'admin_cto::execute$',
}

ORIG_PATH = BASE / 'original.so'


def short(name):
    d = demangle(name)
    d = re.sub(r'pump_recovered::', '', d)
    return d if len(d) <= 110 else d[:107] + '...'


def direct_calls(raw, addr):
    out = []
    i = 0
    while i < len(raw):
        op = raw[i]
        if op == 0x18:
            i += 16; continue
        if op == 0x85:
            imm = struct.unpack_from('<i', raw, i + 4)[0]
            if raw[i + 1] >> 4 == 1 and imm != -1:
                out.append((addr + i, addr + i + 8 + imm * 8))
            else:
                out.append((addr + i, ('syscall', imm & 0xffffffff)))
        i += 8
    return out


ARG_RE = re.compile(r'^(?!j|call|exit|st)(?:\w+)\s+(r[1-5]|w[1-5])\b')


def norm_text(t):
    t = re.sub(r'\s*<[^>]*>', '', t)
    t = re.sub(r'0x[0-9a-f]{5,}', 'ADDR', t)  # lddw section pointers
    t = re.sub(r'call -?0x[0-9a-f]+', 'call X', t)
    t = re.sub(r'\b[rw][6-9]\b', 'rS', t)  # callee-saved register choice is allocation noise
    return t


class Image:
    def __init__(self, path, funcs):
        self.path = Path(path)
        self.blob = self.path.read_bytes()
        self.secs = sections(self.blob)
        self.funcs = funcs  # start -> (size, [names])
        self._txt = {}

    def raw(self, s):
        return body(self.blob, self.secs, s, self.funcs[s][0])

    def text(self, s):
        if s not in self._txt:
            self._txt[s] = objdump_text(self.path, s, s + self.funcs[s][0])
        return self._txt[s]

    def calls(self, s):
        return direct_calls(self.raw(s), s)


def arg_setup(img, s, call_sites):
    """For each call site: normalized text of insns since the previous call that write r1-r5 (last write per reg)."""
    txt = img.text(s)
    addrs = sorted(txt)
    idx = {a: k for k, a in enumerate(addrs)}
    res = {}
    prev = 0
    for cs in call_sites:
        k = idx.get(cs)
        if k is None:
            res[cs] = []; continue
        regs = {}
        for a in addrs[prev:k]:
            t = txt[a]
            m = ARG_RE.match(t)
            if m:
                regs[m.group(1)[1]] = norm_text(t)
        res[cs] = [regs[r] for r in sorted(regs)]
        prev = k + 1
    return res


def ratio(img_a, a, img_b, b):
    ta = [x[2] for x in insns(img_a.raw(a), a, img_a.secs)]
    tb = [x[2] for x in insns(img_b.raw(b), b, img_b.secs)]
    return difflib.SequenceMatcher(None, ta, tb, autojunk=False).ratio()


def load_pairs(path):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate pair key: {key}')
            result[key] = value
        return result
    data = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    if not isinstance(data, dict) or not data:
        raise ValueError('pairs must be a nonempty JSON object')
    pairs = {}
    for key, pattern in data.items():
        address = int(key, 0)
        if address < 0 or address in pairs or not isinstance(pattern, str) or not pattern:
            raise ValueError('invalid or duplicate pair address/pattern')
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f'invalid pair regex: {pattern}') from exc
        pairs[address] = pattern
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', type=Path, required=True)
    ap.add_argument('--json', type=Path)
    ap.add_argument('--md', type=Path)
    ap.add_argument('--only')
    ap.add_argument('--pairs', type=Path, help='JSON object mapping original addresses to symbol regexes')
    ap.add_argument('--depth', type=int, default=6, help='identity refinement rounds (0 = body hash only)')
    a = ap.parse_args()

    pairs = PAIRS if a.pairs is None else load_pairs(a.pairs)
    wins = original_windows()
    missing = set(pairs) - {w['start'] for w in wins}
    if missing:
        ap.error('pair addresses absent from inventory: ' + ', '.join(hex(x) for x in sorted(missing)))
    ofuncs = {w['start']: (w['bytes'], []) for w in wins}
    O = Image(ORIG_PATH, ofuncs)
    cfl = candidate_functions(a.cand)
    cfuncs = {}
    for s, n, nm in cfl:
        cfuncs.setdefault(s, (n, []))[1].append(nm)
    C = Image(a.cand, cfuncs)

    # identity keys by normalized body hash
    def h(img, s):
        return hashlib.sha256(normalize(img.raw(s), s, img.secs)).hexdigest()[:16]
    ohash = {s: h(O, s) for s in ofuncs}
    chash = {s: h(C, s) for s in cfuncs}
    # Weisfeiler-Lehman style refinement: a function's identity includes its callees' identities
    # (normalized hashes mask call immediates, so e.g. ToString::to_string<A> and <B> collide).
    # Unmatched targets are pinned by explicit pairing below, so refine after pairing is known.
    c_by_hash = defaultdict(list)
    for s, hh in chash.items():
        c_by_hash[(cfuncs[s][0], hh)].append(s)
    o_by_hash = defaultdict(list)
    for s, hh in ohash.items():
        o_by_hash[(ofuncs[s][0], hh)].append(s)

    # pair the unmatched windows
    pair = {}
    for o, rx in pairs.items():
        cs = [s for s, (n, nms) in cfuncs.items() if any(re.search(rx, demangle(x)) for x in nms)]
        if not cs:
            ap.error(f'no candidate matches pair {o:#x}: {rx}')
        best = max(cs, key=lambda c: ratio(O, o, C, c))
        pair[o] = best
    cpair = {c: o for o, c in pair.items()}

    ocall_t = {s: [t for _, t in O.calls(s) if not isinstance(t, tuple)] for s in ofuncs}
    ccall_t = {s: [t for _, t in C.calls(s) if not isinstance(t, tuple)] for s in cfuncs}
    for s in pair:
        ohash[s] = 'T%x' % s
    for s in cpair:
        chash[s] = 'T%x' % cpair[s]
    for _ in range(a.depth):
        no = {s: ohash[s] if s in pair else hashlib.sha256((ohash[s] + ','.join(ohash.get(t, '?') for t in ocall_t[s])).encode()).hexdigest()[:16] for s in ofuncs}
        nc = {s: chash[s] if s in cpair else hashlib.sha256((chash[s] + ','.join(chash.get(t, '?') for t in ccall_t[s])).encode()).hexdigest()[:16] for s in cfuncs}
        ohash, chash = no, nc
    c_by_hash = defaultdict(list)
    for s, hh in chash.items():
        c_by_hash[(cfuncs[s][0], hh)].append(s)
    o_by_hash = defaultdict(list)
    for s, hh in ohash.items():
        o_by_hash[(ofuncs[s][0], hh)].append(s)

    def okey(s):
        if s in pair:
            return 'T:%x' % s
        if s not in ofuncs:
            return 'O?:%x' % s
        m = c_by_hash.get((ofuncs[s][0], ohash[s]))
        return 'H:' + ohash[s] if m else 'O!:%x' % s

    def ckey(s):
        if s in cpair:
            return 'T:%x' % cpair[s]
        if s not in cfuncs:
            return 'C?:%x' % s
        m = o_by_hash.get((cfuncs[s][0], chash[s]))
        return 'H:' + chash[s] if m else 'C:%x' % s

    def kname(k):
        if k.startswith('T:'):
            o = int(k[2:], 16)
            return 'TARGET ' + short(cfuncs[pair[o]][1][0])
        if k.startswith('H:'):
            hh = k[2:]
            for (n, x), ss in c_by_hash.items():
                if x == hh:
                    return short(cfuncs[ss[0]][1][0])
        if k.startswith('C:'):
            return short(cfuncs[int(k[2:], 16)][1][0]) + ' [ours-only]'
        if k.startswith('O!:'):
            return 'orig-unmatched@' + k[3:]
        return k

    # global call-graph facts
    ocallers = defaultdict(set)
    for s in ofuncs:
        for site, t in O.calls(s):
            if not isinstance(t, tuple):
                ocallers[okey(t)].add(s)
    ccallers = defaultdict(set)
    for s in cfuncs:
        for site, t in C.calls(s):
            if not isinstance(t, tuple):
                ccallers[ckey(t)].add(s)
    okeys_all = {okey(s) for s in ofuncs}
    ckeys_all = {ckey(s) for s in cfuncs}

    def callee_keys_orig(k):
        if k.startswith('T:'):
            s = int(k[2:], 16)
        elif k.startswith('H:'):
            ss = [s for s in ofuncs if ohash[s] == k[2:]]
            if not ss:
                return []
            s = ss[0]
        else:
            return []
        return [okey(t) for _, t in O.calls(s) if not isinstance(t, tuple)]

    def callee_keys_cand(k):
        if k.startswith('T:'):
            s = pair[int(k[2:], 16)]
        elif k.startswith('H:'):
            ss = [s for s in cfuncs if chash[s] == k[2:]]
            if not ss:
                return []
            s = ss[0]
        elif k.startswith('C:'):
            s = int(k[2:], 16)
        else:
            return []
        return [ckey(t) for _, t in C.calls(s) if not isinstance(t, tuple)]

    only = {int(x, 0) for x in a.only.split(',')} if a.only else None
    report = {'schema': 'pump-main-callgraph-census-v1', 'candidate': str(a.cand),
              'candidate_sha256': hashlib.sha256(C.blob).hexdigest(),
              'method': 'direct call target = site+8+imm*8; callee identity = normalized-body sha256 (score.py masking) with explicit pairing of unmatched windows; difflib alignment of callee key sequences',
              'targets': []}
    md = []
    for o in sorted(pairs, key=lambda x: -ratio(O, x, C, pair[x])):
        if only and o not in only:
            continue
        c = pair[o]
        r = ratio(O, o, C, c)
        oc = O.calls(o); cc = C.calls(c)
        ocalls = [(site, t) for site, t in oc if not isinstance(t, tuple)]
        ccalls = [(site, t) for site, t in cc if not isinstance(t, tuple)]
        osys = Counter('%08x' % t[1] for _, t in oc if isinstance(t, tuple))
        csys = Counter('%08x' % t[1] for _, t in cc if isinstance(t, tuple))
        ok = [okey(t) for _, t in ocalls]
        ck = [ckey(t) for _, t in ccalls]
        oargs = arg_setup(O, o, [s for s, _ in ocalls])
        cargs = arg_setup(C, c, [s for s, _ in ccalls])
        sm = difflib.SequenceMatcher(None, ok, ck, autojunk=False)
        aligned, missing, extra = [], [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    os_, cs_ = ocalls[i1 + k][0], ccalls[j1 + k][0]
                    oa, ca = oargs.get(os_, []), cargs.get(cs_, [])
                    shape = lambda xs: [re.sub(r'r10 - 0x[0-9a-f]+', 'r10 - STK', re.sub(r'(add64 r1, )-0x[0-9a-f]+', r'\1-STK', x)) for x in xs]
                    aligned.append({'callee': kname(ok[i1 + k]), 'orig_site': hex(os_ - o), 'cand_site': hex(cs_ - c),
                                    'args_equal': oa == ca, 'args_shape_equal': shape(oa) == shape(ca),
                                    **({} if oa == ca else {'orig_args': oa, 'cand_args': ca})})
            else:
                for k in range(i1, i2):
                    missing.append((i1, k, ok[k], ocalls[k][0] - o))
                for k in range(j1, j2):
                    extra.append((j1, k, ck[k], ccalls[k][0] - c))
        omult, cmult = Counter(ok), Counter(ck)
        multiset_diff = []
        for k in sorted(set(omult) | set(cmult), key=lambda k: kname(k)):
            if omult[k] != cmult[k]:
                d = {'callee': kname(k), 'key': k, 'orig': omult[k], 'ours': cmult[k]}
                # classification
                in_o, in_c = k in okeys_all, k in ckeys_all
                if omult[k] > cmult[k]:
                    if not in_c:
                        d['kind'] = 'orig-outlines; helper absent from our binary'
                    elif cmult[k] == 0:
                        d['kind'] = 'orig-calls; we inline or drop (helper exists standalone in our build)'
                    else:
                        d['kind'] = 'orig calls it more often'
                    # depth-2: did we inline it? its callees should appear extra in ours
                    sub = Counter(callee_keys_orig(k))
                    extra_ours = Counter(cmult) - Counter(omult)
                    d['depth2_callees'] = [kname(x) for x in sub]
                    d['depth2_seen_as_extra_in_ours'] = [kname(x) for x in sub if extra_ours.get(x)]
                    d['orig_callers'] = len(ocallers.get(k, ()))
                    d['our_callers'] = len(ccallers.get(k, ()))
                else:
                    if not in_o:
                        d['kind'] = 'we outline; no such function in original (orig inlines it)'
                    elif omult[k] == 0:
                        d['kind'] = 'we call; orig inlines here (function exists standalone in orig)'
                    else:
                        d['kind'] = 'we call it more often'
                    sub = Counter(callee_keys_cand(k))
                    extra_orig = Counter(omult) - Counter(cmult)
                    d['depth2_callees'] = [kname(x) for x in sub]
                    d['depth2_seen_as_extra_in_orig'] = [kname(x) for x in sub if extra_orig.get(x)]
                    d['orig_callers'] = len(ocallers.get(k, ()))
                    d['our_callers'] = len(ccallers.get(k, ()))
                multiset_diff.append(d)
        # reorder: keys whose multiset is equal but which lie in non-equal blocks
        reordered = sorted({kname(k) for _, _, k, _ in missing if omult[k] == cmult[k]})
        arg_diffs = [x for x in aligned if not x['args_equal']]
        shape_diffs = [x for x in aligned if not x['args_shape_equal']]
        t = {'original': hex(o), 'orig_bytes': ofuncs[o][0], 'candidate': short(cfuncs[c][1][0]), 'cand_start': hex(c),
             'cand_bytes': cfuncs[c][0], 'ratio': round(r, 4),
             'calls': {'orig': len(ok), 'ours': len(ck), 'aligned': len(aligned), 'orig_syscalls': dict(osys), 'our_syscalls': dict(csys)},
             'orig_sequence': [{'site': hex(s - o), 'callee': kname(k)} for (s, _), k in zip(ocalls, ok)],
             'our_sequence': [{'site': hex(s - c), 'callee': kname(k)} for (s, _), k in zip(ccalls, ck)],
             'multiset_diff': multiset_diff, 'reordered_equal_count': reordered,
             'unaligned_orig': [{'pos': k, 'site': hex(site), 'callee': kname(key)} for _, k, key, site in missing],
             'unaligned_ours': [{'pos': k, 'site': hex(site), 'callee': kname(key)} for _, k, key, site in extra],
             'aligned_arg_setup_diffs': len(arg_diffs), 'aligned_arg_shape_diffs': len(shape_diffs), 'aligned': aligned}
        # error-message formatting form per Source line: 'fmt' = ToString inlined (direct Display::fmt),
        # 'to_string' = outlined ToString::to_string call
        def err_forms(img, start, calls_, keys):
            cs = sorted(source_sites(img.blob, img.secs, start, img.raw(start)), key=lambda x: x['slot'])
            out = []
            for (site, _), k in zip(calls_, keys):
                nm = kname(k)
                form = 'fmt' if 'core::fmt::Display>::fmt' in nm and ('PumpError' in nm or 'ErrorCode' in nm) else 'to_string' if 'ToString>::to_string' in nm else None
                if not form:
                    continue
                off = site - start
                nxt = [c for c in cs if off < c['slot'] <= off + 0x400]
                out.append({'site': hex(off), 'form': form, 'line': (nxt[0]['path'].split('/')[-1] + ':' + str(nxt[0]['line'])) if nxt else None})
            return out
        ef_o, ef_c = err_forms(O, o, ocalls, ok), err_forms(C, c, ccalls, ck)
        by_o = defaultdict(list); by_c = defaultdict(list)
        for x in ef_o: by_o[x['line']].append(x['form'])
        for x in ef_c: by_c[x['line']].append(x['form'])
        flips = [{'line': ln, 'orig': sorted(by_o.get(ln, [])), 'ours': sorted(by_c.get(ln, []))}
                 for ln in sorted(set(by_o) | set(by_c), key=str) if sorted(by_o.get(ln, [])) != sorted(by_c.get(ln, []))]
        t['error_format_forms'] = {'orig': ef_o, 'ours': ef_c, 'differing_lines': flips}

        # inlined AccountInfo::clone estimate: Rc strong-count increments `ldxdw rX,[rY+0]; add64 rX,1`
        # (two per clone: lamports and data). Inlined = hot site (>= 2 % entry freq), called = cold.
        def rc_incs(img, start):
            txt = img.text(start); ad = sorted(txt); n = []
            for k in range(1, len(ad)):
                if re.match(r'add64 (r\d+), 0x1$', txt[ad[k]]) and re.match(r'ldxdw ' + re.match(r'add64 (r\d+)', txt[ad[k]]).group(1) + r', \[r\d+ \+ 0x0\]$', txt[ad[k - 1]]):
                    n.append(hex(ad[k] - start))
            return n
        ro, rc = rc_incs(O, o), rc_incs(C, c)
        cl = lambda keys: sum(1 for k in keys if 'AccountInfo as core::clone::Clone' in kname(k))
        t['account_info_clones'] = {'orig_called': cl(ok), 'orig_inlined_est': len(ro) // 2, 'ours_called': cl(ck), 'ours_inlined_est': len(rc) // 2,
                                    'orig_rc_increment_sites': ro, 'ours_rc_increment_sites': rc}
        hot_o = sum(1 for x in ef_o if x['form'] == 'fmt'); hot_c = sum(1 for x in ef_c if x['form'] == 'fmt')
        t['hotness'] = {'error_sites_hot_orig': hot_o, 'error_sites_cold_orig': len(ef_o) - hot_o,
                        'error_sites_hot_ours': hot_c, 'error_sites_cold_ours': len(ef_c) - hot_c,
                        'clone_sites_hot_orig': len(ro) // 2, 'clone_sites_cold_orig': cl(ok),
                        'clone_sites_hot_ours': len(rc) // 2, 'clone_sites_cold_ours': cl(ck)}
        report['targets'].append(t)
        md.append(f"## {hex(o)} {t['candidate']}  (orig {ofuncs[o][0]} B / ours {cfuncs[c][0]} B, ratio {r:.3f})\n")
        md.append(f"calls orig {len(ok)} / ours {len(ck)}, aligned {len(aligned)}, arg-setup diffs at aligned sites {len(arg_diffs)} (shape-only, stack offsets masked: {len(shape_diffs)}); syscalls orig {sum(osys.values())} ours {sum(csys.values())}\n")
        if osys != csys:
            md.append(f"syscall multiset differs: orig {dict(osys)} ours {dict(csys)}\n")
        md.append('| callee | orig | ours | kind | depth-2 evidence |\n|---|---:|---:|---|---|')
        for d in multiset_diff:
            ev = d.get('depth2_seen_as_extra_in_ours') or d.get('depth2_seen_as_extra_in_orig') or []
            md.append(f"| `{d['callee']}` | {d['orig']} | {d['ours']} | {d['kind']} | {', '.join('`%s`' % x for x in ev)} |")
        if reordered:
            md.append(f"\nreordered (same count, different position): {', '.join('`%s`' % x for x in reordered)}")
        hz = t['hotness']
        md.append(f"hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig {hz['error_sites_hot_orig']} hot / {hz['error_sites_cold_orig']} cold, ours {hz['error_sites_hot_ours']} / {hz['error_sites_cold_ours']}; AccountInfo::clone orig ~{hz['clone_sites_hot_orig']} hot / {hz['clone_sites_cold_orig']} cold, ours ~{hz['clone_sites_hot_ours']} / {hz['clone_sites_cold_ours']}\n")
        if flips:
            md.append('error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:\n')
            for f in flips:
                md.append(f"- `{f['line']}`: orig {f['orig']} / ours {f['ours']}")
            md.append('')
        md.append('')
        print(f"{hex(o)} r={r:.3f} calls {len(ok)}/{len(ck)} aligned {len(aligned)} msdiff {len(multiset_diff)} argdiff {len(arg_diffs)} shape {len(shape_diffs)}", file=sys.stderr)
    if a.json:
        a.json.write_text(json.dumps(report, indent=1) + '\n')
    if a.md:
        a.md.write_text('\n'.join(md) + '\n')


if __name__ == '__main__':
    main()
