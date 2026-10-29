#!/usr/bin/env python3
"""Parse / permute / rebuild the cashback function's IR and score with llc.

python3 irfn.py list FN.ll            # list blocks with successors and calls
"""
import json, re, subprocess, sys, os, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import irscore  # noqa

B = irscore.B
LLC = [str(B / 'llc'), '-O3', '-mattr=+store-imm,+jmp-ext', '-relocation-model=pic', '-function-sections',
       '-data-sections', '-trap-unreachable', '-no-trap-after-noreturn', '-filetype=obj']
LABEL = re.compile(r'^([A-Za-z0-9_.$\-]+|"[^"]+"):(\s|$)')


def parse(text):
    lines = text.rstrip('\n').split('\n')
    head = lines[0]
    assert lines[-1] == '}'
    body = lines[1:-1]
    blocks = []  # (name, lines)
    cur = None
    for ln in body:
        m = LABEL.match(ln)
        if m:
            cur = [m.group(1), [ln]]
            blocks.append(cur)
        else:
            if cur is None:
                cur = ['__entry', []]
                blocks.append(cur)
            cur[1].append(ln)
    return head, [(n, l) for n, l in blocks]


def succs(lines):
    term = None
    out = []
    joined = '\n'.join(lines)
    # terminator: last non-empty, non-metadata-only line (switch spans multiple lines)
    m = re.search(r'\n  (br|switch|ret|unreachable|resume|invoke)\b[\s\S]*$', '\n' + joined)
    if m:
        term = m.group(0)
        out = re.findall(r'label %([A-Za-z0-9_.$\-]+|"[^"]+")', term)
    return out


def render(head, blocks):
    out = [head]
    for n, l in blocks:
        out.extend(l)
    out.append('}')
    return '\n'.join(out) + '\n'


def build(fn_text, workdir, tag, head_path):
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    ll = wd / f'{tag}.ll'
    ll.write_text(Path(head_path).read_text() + fn_text)
    bc = wd / f'{tag}.bc'
    obj = wd / f'{tag}.o'
    r = subprocess.run([str(B / 'llvm-as'), str(ll), '-o', str(bc)], capture_output=True, text=True)
    if r.returncode:
        return {'error': r.stderr[:500]}
    r = subprocess.run(LLC + [str(bc), '-o', str(obj)], capture_output=True, text=True)
    if r.returncode:
        return {'error': r.stderr[:500]}
    res = irscore.score(obj)
    for p in (ll, bc):
        p.unlink()
    return res


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'list':
        head, blocks = parse(Path(sys.argv[2]).read_text())
        for i, (n, l) in enumerate(blocks):
            calls = []
            for x in l:
                m = re.search(r'call [^@]*@"?([^"(]+)"?\(', x)
                if m:
                    nm = m.group(1)
                    if 'llvm.lifetime' in nm or 'llvm.memcpy' in nm and False:
                        continue
                    calls.append(re.sub(r'17h[0-9a-f]{16}E$', '', nm)[-50:])
            print(i, n, len(l), '->', ','.join(succs(l)), '|', ' '.join(c for c in calls if 'lifetime' not in c))


class Fn:
    def __init__(self, path, head='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/lanes/llvm-ir-inverse/work/base/red.head.ll',
                 wd='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/lanes/llvm-ir-inverse/work/runs'):
        self.head, blocks = parse(Path(path).read_text())
        self.blocks = dict(blocks)
        self.order0 = [n for n, _ in blocks]
        self.hp = head
        self.wd = wd
        self.cache = {}

    def idx(self, n):
        return self.order0.index(n)

    def run(self, order, tag='t'):
        key = tuple(order)
        if key in self.cache:
            return self.cache[key]
        assert order[0] == self.order0[0] and sorted(order) == sorted(self.order0)
        txt = render(self.head, [(n, self.blocks[n]) for n in order])
        r = build(txt, self.wd, f'{tag}{os.getpid()}', self.hp)
        self.cache[key] = r
        return r


def move(order, name, pos):
    o = [x for x in order if x != name]
    o.insert(pos, name)
    return o
