import re,os
# MERGE: from:to,...  redirect branches to block 'from' into 'to' and delete 'from'
def edit(f):
    for p in os.environ['MERGE'].split(','):
        a,b=p.split(':')
        m=re.search(r'\n'+re.escape(a)+r':[^\n]*\n.*?unreachable\n',f,re.S); assert m,a
        f=f[:m.start()]+'\n'+f[m.end():]
        f,n=re.subn(r'label %'+re.escape(a)+r'(?=[,\s])','label %'+b,f); assert n>=1,(a,n)
    return f
