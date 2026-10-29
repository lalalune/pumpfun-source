import re,sys
want=int(sys.argv[2]); pat=sys.argv[3]; before=int(sys.argv[4]); after=int(sys.argv[5])
n=0;buf=[]
with open(sys.argv[1],errors='replace') as f:
    for line in f:
        if line.startswith('*** IR Dump'):
            if n==want: break
            n+=1; buf=[line]
        elif n==want: buf.append(line)
L=buf
idx=[i for i,l in enumerate(L) if re.search(pat,l)]
print(L[0].strip())
if idx:
    i=idx[0]; print(''.join(x[:220].rstrip()+'\n' for x in L[max(0,i-before):i+after]))
