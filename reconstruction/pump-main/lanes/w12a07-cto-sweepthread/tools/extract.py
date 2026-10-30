#!/usr/bin/env python3
"""extract.py module.ll out.ll [regex]: keep the body of functions matching regex, turn other defines into declares."""
import sys, re
src, dst = sys.argv[1:3]; pat = re.compile(sys.argv[3] if len(sys.argv) > 3 else r'admin_cto7execute17h')
out = []; skip = False
link = re.compile(r'^define (internal |private |linkonce_odr |weak_odr |hidden |dso_local |unnamed_addr )*')
for line in open(src):
    if skip:
        if line.startswith('}'): skip = False
        continue
    if line.startswith('define '):
        name = re.search(r'@("[^"]+"|[\w.$]+)\(', line).group(1)
        if pat.search(name):
            out.append(re.sub(r'^define internal ', 'define ', line)); continue
        # strip body: header up to '{'
        hdr = line.rstrip().rstrip('{').rstrip()
        hdr = re.sub(r'^define (internal |private )?', 'declare ', hdr)
        hdr = re.sub(r'^declare (linkonce_odr |weak_odr )', 'declare ', hdr)
        hdr = re.sub(r' personality .*$', '', hdr)
        hdr = re.sub(r' !dbg ![0-9]+', '', hdr)
        hdr = re.sub(r' (section|comdat)(\s*"[^"]*"|\([^)]*\))?', '', hdr)
        out.append(hdr + '\n'); skip = True; continue
    out.append(line)
t = ''.join(out)
t = re.sub(r'^(@[\w.$"]+ = )(internal |private )', r'\1', t, flags=re.M)
t = re.sub(r'^@\S+ = [^\n]*\balias\b[^\n]*\n', '', t, flags=re.M)
open(dst, 'w').write(t)
