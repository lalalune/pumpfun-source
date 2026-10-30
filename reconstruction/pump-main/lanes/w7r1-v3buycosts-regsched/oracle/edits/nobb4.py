def edit(f):
    a='bb4:                                              ; preds = %_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit28\n  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i.i29)\n'
    assert a in f
    return f.replace(a,a.split('\n')[0]+'\n')
