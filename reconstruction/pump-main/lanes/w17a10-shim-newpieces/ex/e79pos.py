import json,re
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/e79.py').read().split('V={')[0])
def hdrat(anchor,where='before'):
    def f(t):
        i=t.index('@_ZN14pump_recovered9admin_cto7execute17h'); j=t.index('start:\n',i)
        a=t.index('  '+anchor+' = alloca',j)
        ins='  %e7 = alloca [7 x i8], align 1\n  %e9 = alloca [9 x i8], align 1\n'
        if where=='after': a=t.index('\n',a)+1
        return t[:a]+ins+t[a:]
    return f
def hdrend(t):
    i=t.index('@_ZN14pump_recovered9admin_cto7execute17h'); j=t.index('start:\n',i)
    a=t.index('  %holder = alloca [1 x i8], align 1\n',j); a=t.index('\n',a)+1
    return t[:a]+'  %e7 = alloca [7 x i8], align 1\n  %e9 = alloca [9 x i8], align 1\n'+t[a:]
# best single from screen on e79v base (line-number based edit) -> re-express as text edit: volatile load at validate line
VLV=None
C1A=(VAL,piece('%sharing_update16','%val8'))
base=[(B15,ent()),(A20,ARM),C1A]
V={}
for nm,h in [('top',hdr),('end',hdrend),('b45',hdrat('%_45')),('a45',hdrat('%_45','after')),('bhk',hdrat('%hk')),('bst',hdrat('%st')),('btgt',hdrat('%target')),('bsu',hdrat('%sharing_update')),('bval8',hdrat('%val8')),('bsu16',hdrat('%sharing_update16'))]:
    V['e79p_'+nm]=[h]+base
