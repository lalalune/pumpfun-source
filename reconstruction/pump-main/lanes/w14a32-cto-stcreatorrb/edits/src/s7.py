def T(s):
    a="let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
    i=s.index(a); j=s.index("let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=CtoState{")
    q=s[i+len(a):j]  # quote_locked block
    k=s.index("};",s.index("fee_configurable:a.global.creator_fee_configurable",j))+2
    lit=s[j+len("let (holder,cashback,target,sharing_update,collect_old,skip)={ "):k]
    return s[:i]+q+lit+a+"let (holder,cashback,target,sharing_update,collect_old,skip)={ "+s[k:]
