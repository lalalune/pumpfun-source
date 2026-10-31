import re
EXIT='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
MERGE=__import__('os').environ.get('MERGE','bb49.i bb57.i').split()
def blocks(t):
    # returns dict name->(start,end) of block text
    res={}
    for m in re.finditer(r'\n([\w.$"]+):[^\n]*\n',t):
        res[m.group(1)]=m.start()+1
    return res
def f(t):
    for X in MERGE:
        i=t.index('\n'+X+':')+1; j=t.index('\n\n',i)
        blk=t[i:j]
        phis=re.findall(r'  (%\S+) = phi i64 (.*)',blk)
        preds=re.search(r'preds = (.*)',blk.split('\n')[0]).group(1).split(', ')
        t=t[:i]+t[j+2:]
        # exit phis
        ei=t.index('\n'+EXIT+':')+1; ej=t.index('\n\n',ei); eb=t[ei:ej]
        ephis=re.findall(r'  (%\S+) = phi i64 (.*)',eb)
        neweb=eb
        for k,(en,einc) in enumerate(ephis):
            pn,pinc=phis[k]
            inc=[x for x in re.findall(r'\[ [^\]]+ \]',einc) if not x.endswith('%'+X+' ]')]
            inc+=re.findall(r'\[ [^\]]+ \]',pinc)
            neweb=neweb.replace(f'  {en} = phi i64 {einc}',f'  {en} = phi i64 '+', '.join(inc))
        t=t[:ei]+neweb+t[ej:]
        for p in preds:
            p=p.lstrip('%')
            pi=t.index('\n'+p+':')+1; pj=t.index('\n\n',pi); pb=t[pi:pj]
            t=t[:pi]+pb.replace('label %'+X,'label %'+EXIT)+t[pj:]
    return t
EDITS=[f]
