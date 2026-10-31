import sys,os,difflib,json
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a89-cto-jtnodup/tools'
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['orig_window']()
def toks(raw,fr=False,rg=False):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]; cls=op&7; dst=t[1]&15; s=t[1]>>4
        if fr and cls in (1,2,3) and (dst==10 or s==10): t[2:4]=b'\0\0'
        if rg: t[1]=0
        out.append(bytes(t))
    return out
for f in sys.argv[1:]:
    c=G['elf_fn'](f,G['KEEP']) if f.endswith('.o') or f.endswith('.so') else open(f,'rb').read()
    r=difflib.SequenceMatcher(None,toks(O),toks(c),autojunk=False).ratio()
    fm=difflib.SequenceMatcher(None,toks(O,1),toks(c,1),autojunk=False).ratio()
    rg=difflib.SequenceMatcher(None,toks(O,0,1),toks(c,0,1),autojunk=False).ratio()
    sk=difflib.SequenceMatcher(None,toks(O,1,1),toks(c,1,1),autojunk=False).ratio()
    print(json.dumps({'f':f.split('/')[-2]+'/'+f.split('/')[-1],'bytes':len(c),'ratio':round(r,5),'fm':round(fm,5),'rm':round(rg,5),'sk':round(sk,5)}))
