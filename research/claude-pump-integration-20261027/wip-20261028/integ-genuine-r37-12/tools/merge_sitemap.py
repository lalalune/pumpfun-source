#!/usr/bin/env python3
"""merge_sitemap.py <fresh sitemap.json> <out.json> <extra anchors.json> [...]
A sitemap derived (mksitemap.py) from an UNPADDED build pairs some closures that share one shape with the wrong
instance (manual/file classes pick by candidate order, and same-shape closures in one function are ambiguous before
their lines are fixed). The hand-written extra anchors (coordfiles extra_anchors.json, integ_anchors.json) are
authoritative for the windows they name, so every fresh-sitemap anchor of such a window is dropped here; pins
(already-matched windows) are always kept."""
import json, sys, re
fresh, out, extras = sys.argv[1], sys.argv[2], sys.argv[3:]
covered = set()
for e in extras:
    for a in json.load(open(e))['anchors']:
        if a.get('orig') and a['label'].split(':')[0] in ('new', 'gain', 'pin', 'manual'):
            covered.add(int(a['orig'], 16))
d = json.load(open(fresh))
keep, drop = [], []
for a in d['anchors']:
    cls, _, w = a['label'].partition(':')
    try:
        win = int(w, 16)
    except ValueError:
        win = None
    if cls != 'pin' and win in covered and a.get('orig') is None:
        drop.append(a); continue
    keep.append(a)
d['anchors'] = keep
d.setdefault('notes', []).append(f'merge_sitemap: dropped {len(drop)} fresh anchors of windows covered by extra anchors: '
                                 + ', '.join(sorted({x["label"] for x in drop})))
json.dump(d, open(out, 'w'), indent=1)
print(f'kept {len(keep)}, dropped {len(drop)}:', sorted({x['label'] for x in drop}))
