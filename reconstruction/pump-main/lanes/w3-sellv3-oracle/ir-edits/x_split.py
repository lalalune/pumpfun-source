import os
S=['  %_7 = getelementptr inbounds i8, ptr %a, i64 112\n','  %1 = getelementptr inbounds i8, ptr %a, i64 40\n','; call pump_recovered::extend::prepare_bonding_curve\n','  %_8 = getelementptr inbounds i8, ptr %a, i64 64\n','  %_184 = load ptr']
def edit(f):
    at=S[int(os.environ['SPLITAT'])]
    assert at in f
    return f.replace(at,'  br label %splitbb\n\nsplitbb:\n'+at,1)
