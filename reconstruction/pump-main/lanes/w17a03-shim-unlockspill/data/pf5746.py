EDITS=[("  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(",
        "  let pf:&AccountInfo;crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer("),
       ("lamports:a.pump_fees_event_authority.lamports.clone(),",
        "lamports:unsafe{let r=core::ptr::read(&a.pump_fees_event_authority.lamports);if std::rc::Rc::strong_count(&r)==0{core::hint::unreachable_unchecked()/*shim: count load before the pin*/}pf=core::ptr::read_volatile(&a.pump_fees as *const _ as *const &AccountInfo)/*shim: pins the program clone's pump_fees pointer reload inside the event_authority lamports Rc increment*/;std::rc::Rc::increment_strong_count(std::rc::Rc::as_ptr(&r));r},"),
       ("lamports:a.pump_fees.lamports.clone()",
        "lamports:pf.lamports.clone()")]
