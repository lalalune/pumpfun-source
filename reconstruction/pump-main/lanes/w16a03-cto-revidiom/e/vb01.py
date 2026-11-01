VM=("sharing_update=Some(args.0);","sharing_update=Some(args.0.map(|_|target));")
B01=[("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
     ("*holder_key}else{","holder_key}else{"),
     ("if t==*sharing||t==*holder_key{","if t==*sharing||t==holder_key{"),
     ("unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable","unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st.fee_configurable"),
     ("CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}","CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};}"),
     ("validate(&st,hopt,fee,new,&holder_key,&sk)","validate(&st,hopt,fee,new,holder_key,&sk)")]
EDITS=[VM]+B01
