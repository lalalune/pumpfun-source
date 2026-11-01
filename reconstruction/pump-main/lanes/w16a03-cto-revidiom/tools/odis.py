import re,sys,json,bisect
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom'
def load(path):
    rows=[]; syms={}
    cur=None
    for l in open(path):
        m=re.match(r'^([0-9a-f]{16}) <(.*)>:',l)
        if m: syms[int(m.group(1),16)]=m.group(2); continue
        m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',l)
        if m:
            t=re.sub(r'\s+<[^>]*>','',m.group(2).strip())
            rows.append((int(m.group(1),16),t))
    return rows,syms
if __name__=='__main__':
    which=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); base=int(sys.argv[4],16) if len(sys.argv)>4 else 0x22a10
    rows,_=load(f'{OUT}/dis/{which}.dis')
    for a,t in rows:
        if base+lo<=a<base+hi: print(f'{a-base:#06x}  {t}')
