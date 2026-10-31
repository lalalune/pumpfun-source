#!/usr/bin/env python3
"""region.py <variant fn.bin> [base fn.bin]: where a variant's byte delta lands, by call-anchor alignment against the base
(default: this lane's main capture). Both must have the same call count (154+3). Prints the main-offset intervals whose
size changed and the admin_cto region each falls in. Experiment only."""
import sys,os,json
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
REG=[(0x0,'E entry'),(0x3a8,'V validate+tree'),(0x1a88,'SH sweep head'),(0x26b8,'TC TCF clones/call/Rent'),(0x3c40,'SC sharing-CPI build'),
     (0x4a28,'PC post-CPI pool/event'),(0x5490,'ER error blocks'),(0x5990,'NA sweep native arm'),(0x5bc0,'WA wallet'),(0x6a68,'TL tail')]
def label(o):
    r=REG[0][1]
    for a,n in REG:
        if o>=a: r=n
    return r
def calls(raw):
    out=[];i=0
    while i<len(raw):
        if raw[i]==0x85: out.append(i)
        i+=16 if raw[i]==0x18 else 8
    return out
def regions(var,base=None):
    b=open(base or OUT+'/rx/main/fn.bin','rb').read(); v=open(var,'rb').read()
    cb,cv=calls(b),calls(v)
    if len(cb)!=len(cv): return {'error':f'call count {len(cv)} vs {len(cb)}'}
    cb=cb+[len(b)]; cv=cv+[len(v)]; prev=0; ch=[]; lo=0
    for k in range(len(cb)):
        d=cv[k]-cb[k]
        if d!=prev: ch.append((lo,cb[k],d-prev))
        prev=d; lo=cb[k]
    agg={}
    for lo,hi,dd in ch: agg[label(lo)]=agg.get(label(lo),0)+dd
    return {'bytes':len(v),'delta':len(v)-len(b),'changes':[(hex(lo),hex(hi),dd,label(lo)) for lo,hi,dd in ch],'by_region':agg}
if __name__=='__main__':
    print(json.dumps(regions(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)))
