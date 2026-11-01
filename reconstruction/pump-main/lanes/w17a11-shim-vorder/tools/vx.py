#!/usr/bin/env python3
"""vx.py <name> <spec> [--base slim.ll] : pre-opt IR weight edits on validate branches, then fx oracle + errseq.
spec: comma list of BR:q  (q = probability that the edge named by BR's 'hot' side is taken; for error branches q = P(error)).
Branch ids (validate pre-opt, main d4dfb04):"""
import sys,os,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import fx, errseq
OUT=os.path.dirname(T)
# id: (block, kind, value-expected-for-q)
# kind 'br': cond, expected bool (q = P(cond==expected)); 'sw': switch value, expected i64
BR={
 'B284':('start','br','%_9',1),     # err if true
 'Bhr':('bb6','br','%_19',1),       # q=P(hr)
 'B289':('bb7','br','%_20',0),      # err if hopt!=Some(true)
 'Bh14':('bb14','br','%holder',1),
 'Bhr15':('bb15','br','%_19',1),
 'B296':('bb16','br','%_31',0),     # err if !he
 'Bh21':('bb21','br','%holder',1),  # q=P(holder)
 'B306':('bb23','sw','%_52',0),     # err if tag==0
 'B298':('bb22','sw','%_141',1),    # err if tag==1
 'B307':('bb28','br','%_63',1),
 'B312b':('bb39','br','%_80',1),
 'Bh44':('bb44','br','%holder',1),
 'Bf46':('bb46','sw','%99',0),      # q=P(fee None) non-holder
 'Bf45':('bb45','sw','%101',0),     # q=P(fee None) holder
 'B326':('bb48','br','%110',1),
 'B326h':('bb96','br','%152',1),
 'B330':('bb53','br','%_103',1),
 'B334':('bb55','br','%_116',0),
 'B338a':('bb63','br','%164',1),
 'B338b':('bb64','br','%_126',1),
}
def edit(text,spec):
    m=re.search(r'^define [^\n]*admin_cto8validate[^\n]*\{\n',text,re.M); st=m.end(); en=text.index('\n}\n',st)
    body=text[st:en]; lines=body.split('\n')
    blk=None; k=0
    for item in [x for x in spec.split(',') if x]:
        bid,q=item.split(':'); q=float(q)
        b,kind,v,exp=BR[bid]
        # find block
        i=[j for j,l in enumerate(lines) if l.startswith(b+':')][0]
        if b=='start': i=-1
        j=i+1
        while not (lines[j].startswith('  br i1 '+v+',') or lines[j].startswith('  switch i64 '+v+',')): j+=1
        k+=1; nv='%%vx_%d'%k
        if kind=='br':
            assert lines[j].startswith('  br i1 '+v+','),lines[j]
            lines.insert(j,'  %s = call i1 @llvm.expect.with.probability.i1(i1 %s, i1 %s, double %r)'%(nv,v,'true' if exp else 'false',q))
            lines[j+1]=lines[j+1].replace('br i1 '+v+',','br i1 '+nv+',',1)
        else:
            assert lines[j].startswith('  switch i64 '+v+','),lines[j]
            lines.insert(j,'  %s = call i64 @llvm.expect.with.probability.i64(i64 %s, i64 %d, double %r)'%(nv,v,exp,q))
            lines[j+1]=lines[j+1].replace('switch i64 '+v+',','switch i64 '+nv+',',1)
    body='\n'.join(lines)
    t=text[:st]+body+text[en:]
    for d in ('declare i1 @llvm.expect.with.probability.i1(i1, i1, double)','declare i64 @llvm.expect.with.probability.i64(i64, i64, double)'):
        if d.split('(')[0].split()[-1]+'(' not in t: t+='\n'+d+'\n'
    return t
if __name__=='__main__':
    a=sys.argv[1:]; name=a[0]; spec=a[1]; base=OUT+'/cap_m1/slim.ll'
    if '--base' in a: base=a[a.index('--base')+1]
    t=edit(open(base).read(),spec)
    os.environ['LANE_OUT']=OUT
    r=fx.run(t,name,keep='--keep' in a)
    if 'M' in r:
        b=open(OUT+'/fx/'+name+'/fn.bin','rb').read(); e=errseq.analyze(b); v=[x for x in e if x['frm']<0x2000]
        r['from']=' '.join(str(x['line']) for x in sorted(v,key=lambda x:x['frm']))
        r['name_ord']=' '.join(str(x['line']) for x in sorted(v,key=lambda x:(x['name'] if x['name'] is not None else 1e9)))
        import dis
        r['lddw']=sum(1 for o,s in dis.d(b) if s.startswith('lddw'))
    r['spec']=spec
    print(json.dumps(r))
