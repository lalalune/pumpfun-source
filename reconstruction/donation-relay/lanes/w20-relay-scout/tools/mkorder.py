#!/usr/bin/env python3
"""mkorder.py <unstripped.so> <link.map> > ordered.ld: a linker script that lays out .text in the deployed ELF's function order.
Matched functions go in target address order, every other function follows through *(.text*). Link with RELAY_LINKSCRIPT=<ordered.ld> measure.sh ...
Selectors carry this build's symbol hashes, so regenerate after any source change. Rodata stays in natural order."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relay
cand, lm = sys.argv[1:3]
t, c, sy, tf, tn, cn, pair, idx = relay.compare(cand)
sec = {}
pat = re.compile(r'^\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+(\S.*):\((\.text[^)]*)\)\s*$')
for line in open(lm, errors='replace'):
    m = pat.match(line)
    if m:
        sec[int(m.group(1), 16)] = (m.group(5).strip(), m.group(6))
out = ['PHDRS', '{', '  text PT_LOAD ;', '  rodata PT_LOAD ;', '  data PT_LOAD ;', '  dynamic PT_DYNAMIC ;', '}', '', 'SECTIONS', '{', '  . = SIZEOF_HEADERS;', '  .text : {']
miss = 0
for a, _ in tf:
    b = pair.get(a)
    if b is None:
        continue
    s = sec.get(b)
    if s is None:
        miss += 1
        continue
    obj, name = s
    obj = obj.split('/')[-1]
    m = re.match(r'(.*\.rlib)\((.*)\)$', obj)
    if m:
        obj = m.group(1) + ':' + m.group(2)
    out.append(f'    *{obj}("{name}")')
out += ['    *(.text*)', '  } :text', '  .rodata : { *(.rodata*) } :rodata', '  .data.rel.ro : { *(.data.rel.ro*) } :rodata', '  .dynamic : { *(.dynamic) } :dynamic', '  .dynsym : { *(.dynsym) } :data',
        '  .dynstr : { *(.dynstr) } :data', '  .rel.dyn : { *(.rel.dyn) } :data', '  /DISCARD/ : {', '      *(.eh_frame*)', '      *(.gnu.hash*)', '      *(.hash*)', '    }', '}']
print('\n'.join(out))
print(f'{len(pair)} matched, {miss} without a map section', file=sys.stderr)
