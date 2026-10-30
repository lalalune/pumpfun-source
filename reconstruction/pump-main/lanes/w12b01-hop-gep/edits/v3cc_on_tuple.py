A='''let (allowed, global) = { let global: &Global = &a.global; let user = a.user.key(); (!c.is_mayhem_mode && user!=global.whitelist_pda, global) }; require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(global,'''
B='''let allowed = crate::trade::v3_can_cross(&a.global,c,&a.user.key()); require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(&a.global,'''
def edit(t):
    assert t.count(A)==1; return t.replace(A,B)
def tv3(s):
    a='fn v3_can_cross(global:&Global,curve:&BondingCurve,user:&Pubkey)->bool{'
    assert s.count(a)==1; return s.replace(a,'pub(crate) '+a)
extra={'trade_v3.rs': tv3}
