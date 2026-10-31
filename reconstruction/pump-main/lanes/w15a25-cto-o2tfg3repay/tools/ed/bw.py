import re,os
W=os.environ.get('BW','5,3')
LBL=os.environ.get('BWL','br i1 %holder, label %bb22, label %bb23')
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i)
    b=t[i:j]; assert b.count(LBL)==1,b.count(LBL)
    b=b.replace(LBL,LBL+', !prof !9101')
    return t[:i]+b+t[j:]+'\n!9101 = !{!"branch_weights", i32 '+W.split(',')[0]+', i32 '+W.split(',')[1]+'}\n'
EDITS=[f]
