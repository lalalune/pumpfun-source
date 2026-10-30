import re,difflib,collections,sys
B='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sweep/'
exec(open(B+'scripts/stk.py').read().split("d=collections")[0].replace("sys.argv[1]","sys.argv[1]"))
mp=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for a,b in zip(oj[i1:i2],cj[j1:j2]):
            sa=re.findall(r'r10 - (0x[0-9a-f]+)|add64 r\d, -(0x[0-9a-f]+)',a); sb=re.findall(r'r10 - (0x[0-9a-f]+)|add64 r\d, -(0x[0-9a-f]+)',b)
            if sa and sb: mp[int(''.join(sa[0]),16)][int(''.join(sb[0]),16)]+=1
for k in sorted(mp): print(hex(k), ' '.join(f'{hex(v)}x{n}' for v,n in mp[k].most_common()))
