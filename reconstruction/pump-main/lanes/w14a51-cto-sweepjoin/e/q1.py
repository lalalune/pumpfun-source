# oracle: fold bb49.i / bb57.i into sweep exit, keeping their lifetime.end calls (moved into exit)
import re,os
EXIT='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
MERGE=os.environ.get('MERGE','bb49.i bb57.i').split()
LTPOS=os.environ.get('LTPOS','exit')  # exit: move lifetime.ends into exit; drop: drop them
def blk(t,name):
    i=t.index('\n'+name+':')+1; j=t.index('\n\n',i); return i,j
def f(t):
    moved=[]
    for X in MERGE:
        i,j=blk(t,X); b=t[i:j]
        phis=re.findall(r'  (%\S+) = phi i64 (.*)',b)
        preds=re.search(r'preds = (.*)',b.split('\n')[0]).group(1).split(', ')
        moved+= [l for l in b.split('\n') if 'llvm.lifetime.end' in l]
        t=t[:i]+t[j+2:]
        ei,ej=blk(t,EXIT); eb=t[ei:ej]
        for k,(en,einc) in enumerate(re.findall(r'  (%\S+) = phi i64 (.*)',eb)):
            pn,pinc=phis[k]
            inc=[x for x in re.findall(r'\[ [^\]]+ \]',einc) if not x.endswith('%'+X+' ]')]
            inc+=re.findall(r'\[ [^\]]+ \]',pinc)
            eb=eb.replace(f'  {en} = phi i64 {einc}',f'  {en} = phi i64 '+', '.join(inc))
        hdr=eb.split('\n')[0]
        eb=eb.replace(hdr, re.sub(r'preds = .*','preds = '+', '.join([p for p in re.search(r'preds = (.*)',hdr).group(1).split(', ') if p!='%'+X]+preds),hdr))
        t=t[:ei]+eb+t[ej:]
        for p in preds:
            p=p.strip('%')
            if p.startswith('"'): p=p
            pi,pj=blk(t,p); pb=t[pi:pj]
            t=t[:pi]+pb.replace('label %'+X+',','label %'+EXIT+',').replace('label %'+X+'\n','label %'+EXIT+'\n') +t[pj:] if False else t[:pi]+re.sub(r'label %'+re.escape(X)+r'\b(?![.\w])','label %'+EXIT,pb)+t[pj:]
    if LTPOS=='exit':
        seen=[];
        for l in moved:
            k=re.sub(r', !noalias !\d+','',l)
            if k not in [re.sub(r', !noalias !\d+','',s) for s in seen]: seen.append(l)
        ei,ej=blk(t,EXIT); eb=t[ei:ej]; lines=eb.split('\n')
        # insert after phis
        n=max(i for i,l in enumerate(lines) if ' = phi ' in l)+1
        lines=lines[:n]+seen+lines[n:]
        t=t[:ei]+'\n'.join(lines)+t[ej:]
    return t
EDITS=[f]
