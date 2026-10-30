#!/usr/bin/env python3
"""gepwhere.py sh.ll: report the block where complete_fill's 2nd (global) argument is defined, and that block's preds."""
import sys, re
t = open(sys.argv[1]).read()
m = re.search(r'\ndefine[^\n]*multi_hop_curve8swap_hop17h[^\n]*\{\n', t); s = m.end(); e = t.find('\n}\n', s)
body = t[s:e]
blocks = body.split('\n\n')
def label(b):
    l = b.split('\n', 1)[0]; mm = re.match(r'^("[^"]+"|[\w.$]+):', l)
    return (mm.group(1) if mm else 'ENTRY'), l
call = re.search(r'call fastcc void @\S*complete_fill\S*\(ptr [^%]*%(\S+), ptr [^%]*%([\w.]+)', body)
if not call: print('no complete_fill call'); sys.exit()
arg = call.group(2)
defblk = useblk = None
for b in blocks:
    lab, first = label(b)
    if re.search(r'^\s*%' + re.escape(arg) + r' = ', b, re.M): defblk = (lab, first, re.search(r'^\s*%' + re.escape(arg) + r' = .*$', b, re.M).group(0).strip())
    if 'complete_fill' in b and 'call fastcc' in b: useblk = (lab, first)
print('arg %' + arg, '| def:', defblk[0] if defblk else '(param?)', '|', defblk[2][:90] if defblk else '', '| use blk:', useblk[0], '| preds:', re.sub(r'.*preds = ', '', useblk[1]))
