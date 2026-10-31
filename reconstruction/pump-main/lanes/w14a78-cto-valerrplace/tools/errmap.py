import sys,re,struct; sys.path.insert(0,'tools66'); from dis import dis
NM={0x1b5e78:"289",0x1b5e7c:"306",0x1b5f50:'298',0x1b5e08:"326",0x1b5db8:'296',0x1b5e38:'312',0x1b5e04:'307'}
b=open(sys.argv[1],'rb').read(); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
ins=dis(b); tg=set()
for i,t in ins:
    m=re.search(r', ([+-]0x[0-9a-f]+)$',t) or re.match(r'ja ([+-]0x[0-9a-f]+)',t)
    if m and t.split()[0].startswith('j'): tg.add(i+8+int(m.group(1),16)*8)
out=[]; prev_term=True
for k,(i,t) in enumerate(ins):
    if not(lo<=i<hi): continue
    op=t.split()[0]
    if i in tg: out.append(f'L{i:#x}:')
    s=t
    m=re.search(r', ([+-]0x[0-9a-f]+)$',t) or re.match(r'ja ([+-]0x[0-9a-f]+)',t)
    if m and op.startswith('j'): s=t[:m.start(1)]+f'->{i+8+int(m.group(1),16)*8:#x}'
    if op=='lddw':
        v=int(t.split(', ')[1],16)
        if v in NM: s+=f'   ; msg{NM[v]}'
    if op=='stw' and '-0x2b8' in t: s+=f'   ; LINE {int(t.split(", ")[1],16)}'
    out.append(f'  {i:#06x} {s}')
print('\n'.join(out))
