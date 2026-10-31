import sys
for p in sys.argv[1:]:
    b=open(p,'rb').read(); n=sum(1 for i in range(0,len(b),8) if b[i]==0x85); l=sum(1 for i in range(0,len(b),8) if b[i]==0x18)
    print(p.split('/')[-2], 'calls',n,'lddw',l)
