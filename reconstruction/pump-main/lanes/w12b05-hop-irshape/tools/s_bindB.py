def edit(t):
    a="                let allowed = { let global = &*a.global; let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);\n                match complete_fill(&a.global,"
    b="                let global = &*a.global; let allowed = { let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);\n                match complete_fill(global,"
    assert t.count(a)==1
    return t.replace(a,b,1)
