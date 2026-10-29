import re,sys
t=open(sys.argv[1],errors='replace').read()
name=sys.argv[2]; argpat=sys.argv[3]  # regex identifying the call line
chunks=re.split(r'(?=^\*\*\* IR Dump )',t,flags=re.M)
prev=None
for i,c in enumerate(chunks):
    h=c.splitlines()[0]
    if name not in h and 'At Start' not in h: continue
    m=re.search(r'define[^\n]*@'+re.escape(name)+r'\(.*?\n\}',c,re.S)
    if not m: continue
    body=m.group(0); st=[]
    for mm in re.finditer(r'(%\S+) = (?:tail )?call[^\n]*'+argpat+r'[^\n]*\n((?:[^\n]*\n){0,6})',body):
        call=mm.group(1)
        idx=re.findall(r'extractvalue \{ i64, ptr \} '+re.escape(call)+r', (\d)',mm.group(2))
        st.append(''.join(idx))
    s=str(st)
    if s!=prev: print(i,h[:110],s)
    prev=s
