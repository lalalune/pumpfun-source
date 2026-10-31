import re
def info(t):
    # tag phi (i8 with 2 constants) defined at bb26, test icmp ne tag,2 at sharing gate, swept phi
    m=re.search(r'\n  (%\S+) = icmp ne i8 (%_\d+\.sroa\.0\.0), 2\n  br i1 \1, label %(\w+), label %(\w+)\n',t)
    tst,tag,yes,no=m.groups()
    z=re.search(r'\n  (%\d+) = zext i1 '+re.escape(tst)+r' to i8\n',t)
    sw=re.search(r'\n  (%_95\S*) = phi i64 ',t).group(1)
    return dict(tst=tst,tag=tag,yes=yes,no=no,zext=z.group(1),sw=sw,zline=z.group(0))
def evtag(t):
    d=info(t)
    new='\n  %evtag = icmp ne i8 '+d['tag']+', 2\n  '+d['zext']+' = zext i1 %evtag to i8\n'
    return t.replace(d['zline'],new,1)
def fakeuse_at(t,label_re,val):
    # insert empty asm use of val right after the label line of block label
    m=re.search(r'\n'+label_re+r':[^\n]*\n',t); i=m.end()
    return t[:i]+'  call void asm sideeffect "", "r"(i64 '+val+')\n'+t[i:]
def use_line(val,ty='i64'):
    return '  call void asm sideeffect "", "r"('+ty+' '+val+')\n'
def before_cpi(t,line):
    m=re.search(r'\n  %\d+ = call \{ i64, ptr \} @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config',t); i=m.start()+1
    return t[:i]+line+t[i:]
def after_cpi(t,line):
    m=re.search(r'\n  %\d+ = call \{ i64, ptr \} @_ZN14pump_recovered9pump_fees3cpi24admin_cto_sharing_config[^\n]*\n',t); i=m.end()
    return t[:i]+line+t[i:]
def at_block(t,lab,line):
    m=re.search(r'\n'+re.escape(lab)+r':[^\n]*\n',t); i=m.end()
    while t[i:].startswith('  %') and ' = phi ' in t[i:t.index('\n',i)]: i=t.index('\n',i)+1
    return t[:i]+line+t[i:]
def joinlab(t):
    return re.search(r'\n(bb\d+):[^\n]*\n  %_95\S* = phi',t).group(1)
