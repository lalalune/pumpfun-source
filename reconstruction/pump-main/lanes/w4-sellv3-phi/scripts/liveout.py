import re,sys
t=open(sys.argv[1]).read(); sym=sys.argv[2] if len(sys.argv)>2 else 'trade4sell17h'
m=re.search(r'^define[^\n]*'+sym+r'.*?^}',t,re.M|re.S); f=m.group(0)
blocks=re.split(r'\n(?=[\w.]+:)',f)
entry=blocks[1]
defs=[d for d in re.findall(r'^\s+(%[\w.]+) = (?!alloca)',entry,re.M)]+['%ctx','%amount','%min_sol_output']
for d in defs:
    outs=[b.split(':')[0] for b in blocks[2:] if re.search(re.escape(d)+r'(?![.\w])',b)]
    print(d, len(outs), outs[:6])
