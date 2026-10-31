import sys,re
f=0
for l in open(sys.argv[1]):
    if re.match(r'[0-9a-f]+ <.*admin_cto7execute.*>:',l): f=1; continue
    if f and re.match(r'[0-9a-f]+ <(?!LBB).*>:',l): break
    if f and l.startswith('Disassembly of section'): break
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if f and m: print('%04x  %s'%(int(m.group(1))*8,m.group(2).strip()))
