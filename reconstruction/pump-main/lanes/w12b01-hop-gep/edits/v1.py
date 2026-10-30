A='''

                let allowed = { let global = &*a.global; let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,'''
B='''
                let global: &Global = &a.global;
                let allowed = { let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);
                match complete_fill(global,&a.fee_config,fee_config_len,cap,c,'''
def edit(t):
    assert t.count(A)==1; return t.replace(A,B)
