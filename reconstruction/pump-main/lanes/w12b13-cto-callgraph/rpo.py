#!/usr/bin/env python3
"""rpo.py <post-opt .ll>: RPO (successor order as written) of execute's IR blocks; prints the order of
blocks that call From<AnchorError> (with their stored line) and other {i64,ptr}-returning calls."""
import re, sys
t = open(sys.argv[1]).read()
m = re.search(r'\ndefine [^\n]*admin_cto7execute17h[^\n]*\{\n', t)
body = t[m.end():t.index('\n}\n', m.end())]
blocks = re.split(r'\n(?=[\w.$"-]+:)', body)
names = ['%entry'] + ['%' + b.split(':', 1)[0].strip() for b in blocks[1:]]
idx = {n: i for i, n in enumerate(names)}
succ = []
for b in blocks:
    term = [l for l in b.splitlines() if l.strip().startswith(('br ', 'switch ', 'ret', 'unreachable', 'invoke'))]
    s = []
    if term:
        tl = term[-1]
        if tl.strip().startswith('switch'):
            sw = b[b.index(tl.strip()):]
            s = re.findall(r'label (%[\w.$"-]+)', sw)
        else:
            s = re.findall(r'label (%[\w.$"-]+)', tl)
    succ.append([idx[x] for x in s if x in idx])
# iterative DFS postorder, successors in order
seen = set(); post = []
stack = [(0, iter(succ[0]))]; seen.add(0)
while stack:
    n, it = stack[-1]
    nx = next(it, None)
    if nx is None:
        post.append(n); stack.pop()
    elif nx not in seen:
        seen.add(nx); stack.append((nx, iter(succ[nx])))
rpo = post[::-1]
out = []
for n in rpo:
    b = blocks[n]
    for mm in re.finditer(r'= call \{ i64, ptr \} @("[^"]+"|[\w.$]+)\(', b):
        callee = mm.group(1)
        ls = re.findall(r'store i32 (\d{3}),', b)
        short = 'From' if 'AnchorError' in callee else ('FromPE' if 'ProgramError' in callee else re.sub(r'^"?_ZN\d+', '', callee)[:30])
        out.append(f"{short}{':'+ls[-1] if ls and short=='From' else ''}")
print(' '.join(out))
