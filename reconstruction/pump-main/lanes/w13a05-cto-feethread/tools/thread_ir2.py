import sys,re
# thread_ir2.py <in> <out> <mode h|n|hn>: per-arm fee-None threading into the existing tree blocks (no tree duplication)
src,dst,mode=sys.argv[1:4]
t=open(src).read()
def body(name):
    m=re.search(r'\n'+re.escape(name)+r':[^\n]*\n(.*?)\n\n',t,re.S); return m.group(1)
b70=body('bb70')
lines70=[l for l in b70.split('\n') if ' = phi ' not in l]
def mk70(suffix,vals,br):
    out=[]
    for l in lines70:
        if l.strip().startswith('br '): out.append('  '+br); continue
        for k,v in vals.items(): l=re.sub(re.escape(k)+r'(?![\w.])',v,l)
        out.append(l)
    return f'bb70{suffix}:\n'+'\n'.join(out)+'\n\n'
H={'%_51.sroa.0.0.copyload':'0','%target.i.sroa.7.0':'%target.i.sroa.7.0.copyload','%target.i.sroa.8.0':'%target.i.sroa.8.0.copyload'}
N={'%_51.sroa.0.0.copyload':'1','%target.i.sroa.7.0':'%target.i.sroa.7.0.copyload306','%target.i.sroa.8.0':'%target.i.sroa.8.0.copyload307'}
new=''
def rm_inc(var,ty,val,pred):
    global t
    t2=re.sub(r'(\n  '+re.escape(var)+r' = phi '+ty+r' [^\n]*?)(, )?\[ '+re.escape(val)+r', %'+pred+r' \](, )?',lambda m:m.group(1)+(', ' if (m.group(2) and m.group(3)) else ''),t,count=1)
    assert t2!=t,(var,pred); t=t2
if 'h' in mode:
    new+=mk70('H',H,'br i1 %shared.sroa.0.0.off0, label %bb22, label %bb18')
    t=t.replace('br i1 %switch15.i, label %bb70, label %bb90.i','br i1 %switch15.i, label %bb70H, label %bb90.i')
    for v,ty in (('%_51.sroa.0.0.copyload','i8'),('%target.i.sroa.7.0','i64'),('%target.i.sroa.8.0','ptr')): rm_inc(v,ty,H[v],'bb41.i')
if 'n' in mode:
    new+=mk70('N',N,'br i1 %shared.sroa.0.0.off0, label %bb17, label %bb19')
    t=t.replace('br i1 %switch14.i, label %bb70, label %bb44.i','br i1 %switch14.i, label %bb70N, label %bb44.i')
    for v,ty in (('%_51.sroa.0.0.copyload','i8'),('%target.i.sroa.7.0','i64'),('%target.i.sroa.8.0','ptr')): rm_inc(v,ty,N[v],'bb42.i')
# phis in bb18 / bb19 / bb17
def addphis(blk,lines):
    global t
    t=re.sub(r'\n'+re.escape(blk)+r':([^\n]*)\n',lambda m:'\n'+blk+':'+m.group(1)+'\n'+''.join('  '+l+'\n' for l in lines),t,count=1)
p18=[]; p19=[]; p17=[]
if 'h' in mode:
    p18=['%t7_18 = phi i64 [ %target.i.sroa.7.0, %bb70 ], [ %target.i.sroa.7.0.copyload, %bb70H ]','%t8_18 = phi ptr [ %target.i.sroa.8.0, %bb70 ], [ %target.i.sroa.8.0.copyload, %bb70H ]']
    t7_18,t8_18='%t7_18','%t8_18'
else: t7_18,t8_18='%target.i.sroa.7.0','%target.i.sroa.8.0'
if 'n' in mode:
    p19=[f'%t7_19 = phi i64 [ {t7_18}, %bb18 ], [ %target.i.sroa.7.0.copyload306, %bb70N ]',f'%t8_19 = phi ptr [ {t8_18}, %bb18 ], [ %target.i.sroa.8.0.copyload307, %bb70N ]']
    p17=['%c51_17 = phi i8 [ %_51.sroa.0.0.copyload, %bb15 ], [ 1, %bb70N ]']
    t7_19,t8_19='%t7_19','%t8_19'
else: t7_19,t8_19=t7_18,t8_18
if p18: addphis('bb18',p18)
if p19: addphis('bb19',p19)
if p17: addphis('bb17',p17)
# rewrite bb22 phis
def setinc(var,pred,val):
    global t
    t2=re.sub(r'(\n  '+re.escape(var)+r' = phi [^\n]*?\[ )[^,\]]+(, %'+pred+r' \])',lambda m:m.group(1)+val+m.group(2),t,count=1)
    assert t2!=t or val in t,(var,pred); t=t2
setinc('%target.sroa.7.0','bb18',t8_18); setinc('%target.sroa.6.0','bb18',t7_18)
setinc('%target.sroa.7.0','bb19',t8_19); setinc('%target.sroa.6.0','bb19',t7_19)
if p17: setinc('%_401.sroa.0.0','bb17','%c51_17')
if 'h' in mode:
    for var,val in (('%target.sroa.7.0','%target.i.sroa.8.0.copyload'),('%target.sroa.6.0','%target.i.sroa.7.0.copyload'),('%_401.sroa.0.0','0'),('%_402.sroa.0.0.off0','false')):
        t=re.sub(r'(\n  '+re.escape(var)+r' = phi [^\n]*)',lambda m:m.group(1)+f', [ {val}, %bb70H ]',t,count=1)
t=t.replace('\nbb22:','\n'+new+'bb22:',1)
open(dst,'w').write(t)
