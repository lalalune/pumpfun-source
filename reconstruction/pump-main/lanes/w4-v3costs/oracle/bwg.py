import re,os
# BRS: cond:a:b,... (true:false weights)
def edit(f):
    md=[]
    for i,c in enumerate(os.environ['BRS'].split(',')):
        c,a,b=c.split(':')
        f,n=re.subn(r'(  br i1 '+re.escape(c)+r', [^\n]+)',r'\1, !prof !9100%02d'%i,f); assert n==1,c
        md.append('!9100%02d = !{!"branch_weights", i32 %s, i32 %s}'%(i,a,b))
    return f.replace('\n}\n','\n}\n'+'\n'.join(md)+'\n',1)
