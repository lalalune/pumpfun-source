#!/usr/bin/env python3
"""reduce.py IN.ll OUT_PREFIX : split module into (header-with-declarations, target function text).

Writes OUT_PREFIX.head.ll (everything except the target function, other defines turned into
declares) and OUT_PREFIX.fn.ll (target function). Re-join with: head + fn.
"""
import re, sys

SYM = '_ZN18pump_amm_recovered12instructions4swap4sell8cashback17hccb72da5245169afE'
LINK = re.compile(r'^define\s+((?:(?:internal|private|linkonce_odr|weak_odr|linkonce|weak|available_externally|hidden|protected|dso_local|unnamed_addr|local_unnamed_addr)\s+)*)')

src = open(sys.argv[1]).read().split('\n')
out_head, fn = [], []
i = 0
while i < len(src):
    line = src[i]
    if line.startswith('define '):
        j = i
        while src[j] != '}':
            j += 1
        if f'@{SYM}(' in line:
            fn = src[i:j + 1]
        else:
            sig = line
            # strip body, linkage; drop trailing '{', section/comdat/personality not needed
            sig = sig.rstrip()
            assert sig.endswith('{'), sig[:200]
            sig = sig[:-1].rstrip()
            sig = re.sub(r'\s+comdat(\([^)]*\))?', '', sig)
            sig = re.sub(r'\s+section "[^"]*"', '', sig)
            sig = re.sub(r'\s+personality .*$', '', sig)
            sig = re.sub(r'\s+prefix .*$', '', sig)
            sig = re.sub(r'\s+align \d+$', '', sig)
            m = LINK.match(sig)
            mods = m.group(1).split()
            keep = [x for x in mods if x in ('unnamed_addr', 'local_unnamed_addr')]
            sig = 'declare ' + ' '.join(keep + ['']) + sig[m.end():]
            out_head.append(sig)
        i = j + 1
        continue
    out_head.append(line)
    i += 1
open(sys.argv[2] + '.head.ll', 'w').write('\n'.join(out_head) + '\n')
open(sys.argv[2] + '.fn.ll', 'w').write('\n'.join(fn) + '\n')
