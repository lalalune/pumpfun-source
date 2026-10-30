A='''let allowed = { let global = &*a.global; let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(&a.global,'''
B='''let (allowed, global) = { let global: &Global = &a.global; let user = a.user.key(); (!c.is_mayhem_mode && user!=global.whitelist_pda, global) }; require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(global,'''
def edit(t):
    assert t.count(A)==1; return t.replace(A,B)
