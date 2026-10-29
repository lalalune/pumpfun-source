import sys,re
D=sys.argv[1]
names={}
for l in open(D+'/allocas.txt'):
    m=re.match(r'fi#\s*(\d+) (\S+)\s+(\d+) lt=(\d+)',l)
    if m: names[int(m.group(1))]=(m.group(2),m.group(4))
n16=n8=0;first8=None
for l in open(D+'/pei.txt'):
    m=re.match(r'\s*fi#(\d+): size=(\d+), align=\d+, at location \[SP-(\d+)\]',l)
    if not m: continue
    fi,s,loc=map(int,m.groups())
    if fi in names: print(f'fi#{fi:3d} {names[fi][0]:34s} {s:4d} @{loc:#x} lt={names[fi][1]}')
    elif s==8:
        n8+=1; first8=first8 or loc
    else: n16+=1; print(f'fi#{fi:3d} (isel) {s} @{loc:#x}') if n16<=1 else None
print('isel objs',n16,'spill8',n8,'first spill @',hex(first8 or 0))
