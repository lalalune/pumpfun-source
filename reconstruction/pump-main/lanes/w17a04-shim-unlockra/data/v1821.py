EDITS=[("CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,",
        "CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the TCF ctx owner load ahead of the Rc clones*/,key:x.key,")]
