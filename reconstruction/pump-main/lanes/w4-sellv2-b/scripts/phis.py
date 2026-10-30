import sys,re;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/scripts');import irlib
t=open(sys.argv[1]).read();pre,parts,post=irlib.split(t)
for p in parts:
    ph=[l.strip()[:150] for l in p.split('\n') if ' = phi i64' in l and '[ 0,' in l]
    if ph: print(irlib.label(p)); print('   '+'\n   '.join(ph))
