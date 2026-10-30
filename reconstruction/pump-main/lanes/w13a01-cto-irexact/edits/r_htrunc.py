import re
def f(t):
    pat=re.compile(r'^  %holder10 = call noundef zeroext i1 @"_ZN70_\$LT\$core\.\.option\.\.Option\$LT\$T\$GT\$\$u20\$as\$u20\$core\.\.cmp\.\.PartialEq\$GT\$2eq17h[0-9a-f]+E"\(ptr noalias noundef readonly align 1 dereferenceable\(1\) %holder, [^\n]*$',re.M)
    ms=pat.findall(t); assert len(ms)==1,len(ms)
    return pat.sub('  %h_ld = load i8, ptr %holder, align 1\n  %holder10 = trunc i8 %h_ld to i1',t)
EDITS=[f]
