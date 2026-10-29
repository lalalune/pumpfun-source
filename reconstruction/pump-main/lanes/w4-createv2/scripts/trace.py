import re,sys
FN=sys.argv[2]; pat=re.compile(sys.argv[3])
buf=[];hdr=None;prev=None;n=0
def flush():
    global prev
    if hdr is None: return
    body=''.join(buf)
    if FN not in hdr: return
    sig=[l.strip()[:200] for l in body.splitlines() if pat.search(l)]
    s='\n'.join(sig)
    if s!=prev:
        print('#',n,hdr.strip()[:120]); print('   '+s.replace('\n','\n   ')); prev=s
with open(sys.argv[1],errors='replace') as f:
    for line in f:
        if line.startswith('*** IR Dump'):
            flush(); hdr=line; buf=[]; n+=1
        else: buf.append(line)
flush()
