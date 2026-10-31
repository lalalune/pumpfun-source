import sys,os,difflib
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
sys.argv,A=['x','n'],sys.argv
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
O=mask(orig_window()); C=mask(open(A[1],'rb').read())
def offs(t):
    o=[0]
    for x in t: o.append(o[-1]+len(x))
    return o
oo=offs(O); co=offs(C)
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
last=None; MINLEN=int(A[2]) if len(A)>2 else 4
for i,j,n in sm.get_matching_blocks():
    if n<MINLEN: continue
    d=(co[j]-oo[i])//8
    if d!=last: print('orig %#06x ours %#06x drift %+d (block %d)'%(oo[i],co[j],d,n)); last=d
