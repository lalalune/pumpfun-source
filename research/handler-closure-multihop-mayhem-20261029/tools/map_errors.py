import re
import sys

text = open('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained/programs/pump/src/lib.rs').read()
m = re.search(r'pub enum PumpError \{(.*?)\n\}', text, re.S)
body = m.group(1)
index = 0
mapping = {}
for line in body.splitlines():
    line = line.strip()
    mm = re.match(r'^(\w+)\s*(=\s*(\d+))?\s*,?$', line)
    if not mm or not mm.group(1):
        continue
    if mm.group(3):
        index = int(mm.group(3))
    mapping[6000 + index] = mm.group(1)
    index += 1
for code in [int(x) for x in sys.argv[1:]]:
    print(code, mapping.get(code, '?'))
