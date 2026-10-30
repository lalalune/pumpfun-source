#!/usr/bin/env python3
"""trim.py <in.ll> <out.ll>: keep admin_cto::execute's body (and alias targets); every other
definition becomes a declaration (same attributes), so llc parses and codegens one function.
The oracle check (ctoracle.py cmp) proves the trimmed module still reproduces the build."""
import re, sys
src, dst = sys.argv[1:3]
lines = open(src).readlines()
keep = set()
for line in lines:
    if line.startswith('@') and ' alias ' in line:
        m = re.search(r'ptr (@"[^"]+"|@[\w.$]+)\s*$', line.strip())
        if m: keep.add(m.group(1))
out = []; skip = False
for line in lines:
    if skip:
        if line.startswith('}'):
            skip = False
        continue
    if line.startswith('define ') and 'admin_cto7execute17h' not in line.split('(')[0]:
        m = re.search(r'(@"[^"]+"|@[\w.$]+)\(', line)
        if m and m.group(1) not in keep:
            rest = line[len('define '):].rstrip()
            assert rest.endswith('{'), line[:200]
            rest = rest[:-1].rstrip()
            rest = re.sub(r'^(internal|private|linkonce_odr|weak_odr|external)\s+', '', rest)
            rest = re.sub(r' personality ptr @[\w.$"]+', '', rest)
            rest = re.sub(r' !dbg !\d+', '', rest)
            line = 'declare ' + rest + '\n'
            skip = True
    out.append(line)
open(dst, 'w').writelines(out)
print('kept alias targets', len(keep))
