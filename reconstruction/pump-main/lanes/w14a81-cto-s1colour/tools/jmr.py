# jmr.py fn.bin... : plain M and jump-offset-masked jM (frame and regs kept), rx token masking otherwise
import sys,difflib
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a81-cto-s1colour/tools'
g={'__name__':'x'}; s_=open(T+'/rx.py').read(); exec(s_[:s_.index("OUT=os.environ.get")],g)
O=g['orig_window']()
def jm(toks):
    out=[]
    for t in toks:
        if (t[0]&7) in (5,6) and t[0] not in (0x85,0x95): t=t[:2]+b'\0\0'+t[4:]
        out.append(t)
    return out
o=g['mask'](O)
for f in sys.argv[1:]:
    c=g['mask'](open(f,'rb').read())
    a=difflib.SequenceMatcher(None,o,c,autojunk=False); b=difflib.SequenceMatcher(None,jm(o),jm(c),autojunk=False)
    M=sum(x.size for x in a.get_matching_blocks()); JM=sum(x.size for x in b.get_matching_blocks())
    print(f.split('/')[-2],len(open(f,'rb').read()),round(a.ratio(),5),M,round(b.ratio(),5),JM)
