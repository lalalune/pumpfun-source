import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from q1 import *
EQ=r'call noundef zeroext i1 @"_ZN70_\$LT\$core\.\.option\.\.Option\$LT\$T\$GT\$\$u20\$as\$u20\$core\.\.cmp\.\.PartialEq\$GT\$2eq17hf076679b4972164dE"\([^\n]*'
VAL='admin_cto8validate'; EXE='admin_cto7execute17'
def infn(name):
    def deco(f):
        def g(t):
            m=re.search(r'^define [^\n]*'+name+r'[^\n]*\{\n',t,re.M); e=t.index('\n}\n',m.end())+3
            return t[:m.start()]+f(t[m.start():e])+t[e:]
        return g
    return deco
def sub1(t,pat,rep_,n=1):
    t2,c=re.subn(pat,rep_,t); assert c==n,(pat,c); return t2
@infn(VAL)
def vlate(t):
    t=sub1(t,r'  %holder = '+EQ+'\n','')
    a="bb6:                                              ; preds = %start\n"
    t=rep(t,a,a+"  %holder = trunc i8 %0 to i1\n")
    t=sub1(t,r'%_22 = '+EQ,'%_22 = or i1 %holder, false')
    return t
@infn(EXE)
def e23(t):
    a="bb23:                                             ; preds = %bb83\n  br i1 %_holder, label %bb24, label %bb25\n"
    return rep(t,a,"bb23:                                             ; preds = %bb83\n  %h23 = trunc i8 %106 to i1\n  br i1 %h23, label %bb24, label %bb25\n")
if __name__=='__main__':
    run('q2a',vlate)
    run('q2b',lambda t:e23(vlate(t)))
