import sys,re
# names.py <mn.ll>: TCF clone pointer SSA names in source order (11 plain/hand clones)
L=open(sys.argv[1]).read().split('\n')
s=next(i for i,l in enumerate(L) if re.match(r'  %x\.i = load ptr',l))
out=[]
for i in range(s,s+700):
    m=re.match(r'  (%\S+) = load ptr, ptr (%\S+), align 8, !noalias !\d+, !nonnull !2, !align !3, !noundef !2$',L[i])
    if m and not re.match(r'%_(59|186)\.',m.group(1)):
        # must be followed by key load from it within 3 lines
        if any(re.match(r'  %\S+ = load ptr, ptr '+re.escape(m.group(1))+', align 8',L[j]) for j in range(i+1,i+20)): out.append(m.group(1))
print('\n'.join(out))
