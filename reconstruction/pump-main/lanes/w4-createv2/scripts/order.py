import sys
src=open(sys.argv[1]).read(); order=sys.argv[3].split(',')
i=src.index('fn init_curve('); body=src[i:]
lines=body.split('\n')
stores=[l for l in lines if l.startswith(' bonding_curve.')]
key=lambda l: l.split('.')[1].split('=')[0]
d={key(l):l for l in stores}
assert set(order)==set(d),(set(order)^set(d))
new='\n'.join(d[k] for k in order)+'\n'; old='\n'.join(stores)+'\n'
open(sys.argv[2],'w').write('EDITS=[(%r,%r)]\n'%(old,new))
