import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
os.environ['KEEP']='0'
from h4 import *
def mk(sw,pads,tag=1):
    t=h7(base)
    if tag: t=tag1(t)
    if sw: t=swap87(t)
    for j,(b,w) in enumerate(pads):
        t=addpad(t,b,w,200+j)
    return t
def run(name,sw,pads,tag=1):
    t=mk(sw,pads,tag)
    r=score(t,name,ref='m1'); print(json.dumps(r)[:430],flush=True); return r
if __name__=='__main__':
    P45=('bb45.i','head')
    run('u1',1,[('bb7.i','head'),P45,P45,P45,P45])         # size? 
    run('u2',1,[('bb8.i','head'),('bb7.i','head'),P45,P45,P45])
    run('u3',1,[('bb8.i','head'),P45,P45,P45,P45])
    run('u4',1,[('bb8.i','tail'),('bb7.i','tail'),P45,P45,P45])
