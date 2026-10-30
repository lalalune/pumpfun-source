import re,os
def edit(f):
    for c in os.environ['BRS'].split(','):
        f,n=re.subn(r'(  br i1 '+re.escape(c)+r', [^\n]+)',r'\1, !prof !900000',f); assert n==1,c
    a,b=os.environ.get('W','1:2000').split(':')
    return f.replace('\n}\n','\n}\n!900000 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b),1)
