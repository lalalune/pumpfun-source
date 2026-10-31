import sys,re
L={284,289,296,298,306,307,312,326,330,334,338,410,556,648,660,719}
for f in sys.argv[1:]:
    s=[]
    for l in open(f):
        m=re.match(r'(\w+)\s+stw \[r10-0x2[a-f0-9]{2}\], (\d+)$',l.strip())
        if m and int(m.group(2)) in L: s.append(f'{m.group(2)}@{m.group(1).lstrip("0")}')
    print(f, ' '.join(s[:16]))
