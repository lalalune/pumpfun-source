import sys,re,difflib,collections
sys.argv=[sys.argv[0]]+sys.argv[1:]
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-adminCTO/scripts/offmap.py').read().split('o=load(sys.argv[1])')[0])
o=load(sys.argv[1]); c=load(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
d=collections.Counter(); tot=0; eq=0
reg=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for k in range(i2-i1):
            for oo,cc in zip(o[i1+k][2],c[j1+k][2]):
                tot+=1; eq+=(oo==cc); d[cc-oo]+=1; reg[oo//0x100][cc-oo]+=1
print('offset pairs',tot,'equal',eq)
for k in sorted(reg): print(f'orig {k*0x100:#06x}..: '+' '.join(f'{dd:+#x}:{n}' for dd,n in reg[k].most_common(4)))
