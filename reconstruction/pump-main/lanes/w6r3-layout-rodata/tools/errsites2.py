import re,sys
def run(f,NAME,DISP,TS):
    L=[l.rstrip() for l in open(f)]
    calls={}
    for i,l in enumerate(L):
        m=re.match(r'(0x\w+)\s+call (-?0x\w+)',l)
        if m: calls[i]=int(m.group(1),16)+8+int(m.group(2),16)*8
    out=[]
    for i,l in enumerate(L):
        m3=re.search(r'stw \[r10 - 0x238\], (0x1[78]\w\w)$',l)
        if not m3: continue
        line=None
        for j in range(i-6,i+6):
            m4=re.search(r'stw \[r10 - 0x2b8\], (0x\w+)$',L[j]); 
            if m4: line=int(m4.group(1),16)
        # walk back to block start: previous 'ja' or label
        kinds=[]
        for j in range(i-1,max(0,i-70),-1):
            if re.search(r'\sja |exit',L[j]): break
            if j in calls: kinds.append({NAME:'N',DISP:'D',TS:'T'}.get(calls[j],'x'))
        out.append((L[i].split()[0],m3.group(1),line,''.join(reversed(kinds))))
    return out
for r in run(sys.argv[1],0x157380,0x15de88,0xa938): print('O',r)
for r in run(sys.argv[2],0x1575a8,0x15e0b0,0xa850): print('C',r)
