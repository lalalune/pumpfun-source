EDITS=[("  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(",
        "  let pf:&AccountInfo;crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer("),
       ("key:a.pump_fees_event_authority.key,",
        "key:{pf=unsafe{core::ptr::read_volatile(&a.pump_fees as *const _ as *const &AccountInfo)}/*shim: pins the program clone's pump_fees pointer reload after the event_authority lamports clone*/;a.pump_fees_event_authority.key},"),
       ("lamports:a.pump_fees.lamports.clone()",
        "lamports:pf.lamports.clone()")]
