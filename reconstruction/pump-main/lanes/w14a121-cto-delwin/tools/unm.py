import sys,os,difflib
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from bdis import decode
exec(open(D+'/rx.py').read().split('OUT=os.environ')[0].replace("sys.argv[1:]","[]"))
f=sys.argv[1]; lo=int(sys.argv[2],0); hi=int(sys.argv[3],0); side=sys.argv[4]
O=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a121-cto-delwin/orig.bin'),'rb').read(); c=open(f,'rb').read()
oi=decode(O); ci=decode(c)
o=mask(O); cc=mask(c)
sm=difflib.SequenceMatcher(None,o,cc,autojunk=False)
for tag,a1,a2,b1,b2 in sm.get_opcodes():
    if tag=='equal': continue
    if side=='ours':
        for k in range(b1,b2):
            if lo<=ci[k]['off']<hi: print('%s ours %05x %-30s'%(tag,ci[k]['off'],ci[k]['txt']), ' | orig@%05x'%oi[min(a1,len(oi)-1)]['off'])
    else:
        for k in range(a1,a2):
            if lo<=oi[k]['off']<hi: print('%s orig %05x %-30s'%(tag,oi[k]['off'],oi[k]['txt']), ' | ours@%05x'%ci[min(b1,len(ci)-1)]['off'])
