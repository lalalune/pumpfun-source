#!/usr/bin/env python3
"""trim2.py <trimmed.ll> <out.ll>: second pass after trim.py: drop declarations and globals that
execute (and the kept alias targets) never reference, and every metadata node not reachable from
the kept text or named metadata. Validate with ctoracle.py cmp."""
import re, sys
src, dst = sys.argv[1:3]
lines = open(src).read().split('\n')
# top-level entities
md = {}; other = []; i = 0
while i < len(lines):
    l = lines[i]
    m = re.match(r'^!(\d+) = ', l)
    if m:
        md[m.group(1)] = l; i += 1; continue
    other.append(l); i += 1
text = '\n'.join(other)
# drop unreferenced declarations / globals (iterate to fixpoint)
def name_of(l):
    m = re.match(r'^(?:declare|define)[^@]*(@"[^"]+"|@[\w.$]+)\(', l)
    if m: return m.group(1)
    m = re.match(r'^(@"[^"]+"|@[\w.$]+) = ', l)
    if m: return m.group(1)
    return None
changed = True
while changed:
    changed = False
    body = '\n'.join(other)
    keep = []
    for l in other:
        nm = name_of(l)
        if nm and (l.startswith('declare') or (l.startswith('@') and ' alias ' not in l)):
            cnt = body.count(nm + '(') + body.count(nm + ',') + body.count(nm + ' ') + body.count(nm + ')') + body.count(nm + '\n')
            own = l.count(nm)
            if cnt - own <= 0 and not l.startswith('@llvm.'):
                changed = True; continue
        keep.append(l)
    other = keep
text = '\n'.join(other)
seen = set(); stack = re.findall(r'!(\d+)\b', text)
while stack:
    k = stack.pop()
    if k in seen or k not in md: continue
    seen.add(k); stack.extend(re.findall(r'!(\d+)\b', md[k][len(k) + 1:]))
out = other + [md[k] for k in sorted(seen, key=int)]
open(dst, 'w').write('\n'.join(out) + '\n')
print('metadata kept', len(seen), 'of', len(md), 'lines', len(out))
