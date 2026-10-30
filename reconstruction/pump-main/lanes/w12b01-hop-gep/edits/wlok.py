A='''let allowed = { let global = &*a.global; let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);'''
B='''let allowed = whitelist_ok(&a.global,a.user.key(),c); require!(allowed,PumpError::NotEnoughTokensToBuy);'''
P='''            remaining, true)?.map(|post| (fees, quote, post)))
        }
\n'''
Q='''            remaining, true)?.map(|post| (fees, quote, post)))
        }
        fn whitelist_ok(global: &Global, user: Pubkey, curve: &BondingCurve) -> bool { !curve.is_mayhem_mode && user != global.whitelist_pda }
'''
def edit(t):
    assert t.count(A)==1; t=t.replace(A,B)
    assert t.count(P)==1; t=t.replace(P,Q)
    return t
