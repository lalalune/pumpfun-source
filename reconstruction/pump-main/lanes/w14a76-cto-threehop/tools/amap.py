import sys,os,difflib
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a76-cto-threehop/tools'
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['orig_window']()
def toks(raw):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); cls=t[0]&7; dst=t[1]&15; s=t[1]>>4
        if cls in (1,2,3) and (dst==10 or s==10): t[2:4]=b'\0\0'
        t[1]=0; out.append(bytes(t))
    return out
o=toks(O)
for f in sys.argv[1:]:
    c=toks(open(f,'rb').read())
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    print(f, round(sm.ratio(),4))
    # per 1/16 of orig: fraction matched
    M=[0]*len(o)
    for a,b,n in sm.get_matching_blocks():
        for i in range(a,a+n): M[i]=1
    N=32; L=len(o)
    print(' '.join(f'{sum(M[i*L//N:(i+1)*L//N])*100//max(1,(L//N)):2d}' for i in range(N)))
