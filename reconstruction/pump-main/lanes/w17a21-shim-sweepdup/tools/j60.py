#!/usr/bin/env python3
"""j60.py: fold sweep.exit's Result test into its two predecessors (Err join J60 and Ok join J53) so early
tail-dup sees a {PHI; JNE; JMP} join (post-opt IR edit, experiment only)."""
import re,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import irf,dup2
def j60(t,place60='keep',place53='keep',ne=True,errpos='end'):
    dup2.setnames(t)
    SX=dup2.SX; J60=dup2.J60; OK=dup2.OK; EJ=dup2.EJ
    def f(B,order):
        P=irf.preds(B)
        J53=[p for p in P[SX] if p!=J60][0]
        sx=B[SX]; ph=dup2.phis(sx)
        T60,_=dup2.pick(ph[0][2],'%'+J60); P60,_=dup2.pick(ph[1][2],'%'+J60)
        T53,_=dup2.pick(ph[0][2],'%'+J53); P53,_=dup2.pick(ph[1][2],'%'+J53)
        tagv,payv=ph[0][0],ph[1][0]
        LT=dup2.lt_of(sx)
        # find the Err successor block of SX (bb92)
        brl=[l for l in sx if re.match(r'\s+br i1',l)][0]
        okb,errb=re.findall(r'label %([\w.$"-]+)',brl)
        assert okb==OK
        def tail(name,T,Pv,err):
            if ne: return LT+['  %%%s.c = icmp ne i64 %s, 2'%(name,T),'  br i1 %%%s.c, label %%%s, label %%%s'%(name,err,OK)]
            return LT+['  %%%s.c = icmp eq i64 %s, 2'%(name,T),'  br i1 %%%s.c, label %%%s, label %%%s'%(name,OK,err)]
        # J60
        b=B[J60]; k=[i for i,l in enumerate(b) if re.match(r'\s+br label %',l)][0]
        n60='j60x'
        B[J60]=b[:k]+tail(n60,T60,P60,'j60E')+b[k+1:]
        B['j60E']=['j60E:                                ; preds = %'+J60,'  %%j60p = inttoptr i64 %s to ptr'%P60,'  br label %%%s'%EJ]
        # J53 uses the existing err block, rewritten
        b=B[J53]; k=[i for i,l in enumerate(b) if re.match(r'\s+br label %',l)][0]
        B[J53]=b[:k]+tail('j53x',T53,P53,errb)+b[k+1:]
        eb=B[errb]
        eb=[l.replace(payv,P53) for l in eb]
        eb=[re.sub(r'; preds = .*','; preds = %'+J53,l) if l.startswith(errb+':') else l for l in eb]
        B[errb]=eb
        # OK phi
        ob=B[OK]
        ob=[l.replace('[ %s, %%%s ]'%(payv,SX),'[ %s, %%%s ], [ %s, %%%s ]'%(P60,J60,P53,J53)) for l in ob]
        B[OK]=ob
        # EJ phis: replace tagv from errb with T53, add j60E
        e=B[EJ]; ph=dup2.phis(e); ne_=[]
        for l in e:
            if l==ph[0][3]: l=l+', [ %j60p, %j60E ]'
            elif l==ph[1][3]: l=l.replace('[ %s, %%%s ]'%(tagv,errb),'[ %s, %%%s ]'%(T53,errb))+', [ %s, %%j60E ]'%T60
            ne_.append(l)
        B[EJ]=ne_
        del B[SX]; order.remove(SX)
        order.insert(len(order) if errpos=='end' else order.index(J60)+1,'j60E')
        # placement
        if place60=='beforeok':
            order.remove(J60); order.insert(order.index(OK),J60)
        if place53=='beforeok':
            order.remove(J53); order.insert(order.index(OK),J53)
        if place60=='end': order.remove(J60); order.append(J60)
        if place53=='end': order.remove(J53); order.append(J53)
        return B,order
    return dup2.edit_fn(t,f)
