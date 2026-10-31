# thread selected bb56.i preds straight into bb86 (sweep Err copy block) -- post-opt IR oracle, experiment only
import re,os
SE='%_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def mk(preds):
    def f(t):
        L=t.split('\n')
        def find(lbl):
            for i,l in enumerate(L):
                if l.startswith(lbl+':'): return i
            raise KeyError(lbl)
        i56=find('bb56.i'); p0=L[i56+1]; p1=L[i56+2]
        def take(line,pred):
            m=re.search(r'\[ ([^\]]+?), %'+re.escape(pred.lstrip('%'))+r' \](, )?',line)
            v=m.group(1); line=line.replace(m.group(0),'',1); line=re.sub(r', $','',line).replace(', \n','\n'); return line,v
        tv={};pv={}
        for p in preds:
            p0,tv[p]=take(p0,p); p1,pv[p]=take(p1,p)
        L[i56+1]=p0.rstrip(', ').rstrip(); L[i56+2]=p1.rstrip(', ').rstrip()
        # fix trailing commas
        for k in (i56+1,i56+2): L[k]=re.sub(r',\s*$','',L[k])
        # redirect branches in preds
        for p in preds:
            lbl=p.lstrip('%')
            j=find(lbl) if not lbl.startswith('"') else find(lbl)
            k=j
            while not L[k].lstrip().startswith('br '): k+=1
            assert 'label %bb56.i' in L[k],(p,L[k]); L[k]=L[k].replace('label %bb56.i','label %bb86')
        i86=find('bb86')
        L[i86]=L[i86]+', '+', '.join(preds)
        assert L[i86+1].startswith('  %576 = inttoptr i64 %_428.sroa.18.3 to ptr')
        ph='  %p86 = phi i64 [ %_428.sroa.18.3, '+SE+' ]'+''.join(', [ %s, %s ]'%(pv[p],p) for p in preds)
        th='  %t86 = phi i64 [ %_428.sroa.0.3, '+SE+' ]'+''.join(', [ %s, %s ]'%(tv[p],p) for p in preds)
        L[i86+1]=ph+'\n'+th+'\n  %576 = inttoptr i64 %p86 to ptr'
        t='\n'.join(L)
        t=t.replace('[ %_428.sroa.0.3, %bb86 ]','[ %t86, %bb86 ]')
        return t
    return f
