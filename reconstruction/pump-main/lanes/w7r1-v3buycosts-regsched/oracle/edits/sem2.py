import re,os
K=os.environ['SEM']
def edit(f):
    if K=='mayhemtrunc':
        f=f.replace('  %_10.not = icmp eq i8 %is_mayhem, 0\n','  %mt = trunc i8 %is_mayhem to i1\n  %_10.not = xor i1 %mt, true\n')
    elif K=='mayhemtrunc2':
        f=f.replace('  %_10.not = icmp eq i8 %is_mayhem, 0\n','  %mt = trunc i8 %is_mayhem to i1\n').replace('br i1 %_10.not, label %bb3.i14, label %_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit28','br i1 %mt, label %_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit28, label %bb3.i14')
    elif K=='norange':
        f=re.sub(r', !range !\d+','',f)
    elif K=='notail':
        f=f.replace('tail call','call')
    elif K=='nocallattr':
        f=re.sub(r'\) #27',')',f)
    elif K=='mayhemne':
        f=f.replace('  %_10.not = icmp eq i8 %is_mayhem, 0\n','  %_10.not = icmp ult i8 %is_mayhem, 1\n')
    elif K=='mayhemsgt':
        f=f.replace('  %_10.not = icmp eq i8 %is_mayhem, 0\n','  %_10.not = icmp sle i8 %is_mayhem, 0\n')
    return f
