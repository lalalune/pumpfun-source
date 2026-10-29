#!/usr/bin/env python3
"""Extract distinct line-aligned hunks of historical cashback fns vs pristine (same total line count)."""
import json, re, collections
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
SWARM = LANE.parent.parent
P = (SWARM / 'baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs').read_text().split('\n')
cb0 = next(i for i, l in enumerate(P) if 'fn cashback' in l)
MAC = re.compile(r'\b(require[a-z_]*!|err!|error!)')


def maclines(lines, a, b):
    return [i for i in range(a, b) if MAC.search(lines[i])]


rows = json.loads((LANE / 'work/classify.json').read_text())
H = collections.OrderedDict()
for r in rows:
    t = (LANE / 'src' / f"{r['sha']}.rs").read_text(errors='replace').split('\n')
    if len(t) != len(P):
        continue
    if t[:cb0] != P[:cb0]:
        continue
    i = cb0
    while i < len(P):
        if t[i] != P[i]:
            j = i
            while j < len(P) and t[j] != P[j]:
                j += 1
            # merge hunks separated by <=1 equal blank line
            while j + 1 < len(P) and t[j + 1] != P[j + 1] and P[j].strip() == '':
                j += 1
                while j < len(P) and t[j] != P[j]:
                    j += 1
            new = tuple(t[i:j])
            k = (i + 1, j, new)  # 1-based start, end exclusive(0-based)=end inclusive 1-based
            ok_mac = [x for x in maclines(t, i, j)] == [x for x in maclines(P, i, j)] or \
                set(maclines(t, i, j)) <= set(maclines(P, i, j)) | set(range(i, j))
            if k not in H:
                H[k] = {'start': i + 1, 'end': j, 'new': list(new), 'old': P[i:j], 'n': 0, 'ex': r['sha'],
                        'mac_old': [x + 1 for x in maclines(P, i, j)], 'mac_new': [x + 1 for x in maclines(t, i, j)]}
            H[k]['n'] += 1
            i = j
        else:
            i += 1
out = list(H.values())
(LANE / 'work/hunks.json').write_text(json.dumps(out, indent=1))
print('distinct hunks', len(out))
c = collections.Counter((h['start'], h['end']) for h in out)
for (s, e), n in sorted(c.items()):
    print(s, e, n)
