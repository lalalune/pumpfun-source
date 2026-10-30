#!/usr/bin/env python3
"""var.py <crate_copy> <gene>[,<gene>...]: exact-string source genes on admin_cto.rs (each anchor must occur once;
line count preserved)."""
import sys
from pathlib import Path
CPI = "crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer("
G = {
 'none': [],
 # let-bound mint AccountInfo inside the Some arm, before the CPI expression
 'm_let': [(CPI, "let mint_ai=a.mint.to_account_info();" + CPI), ("mint:a.mint.to_account_info(),sharing_config", "mint:mint_ai,sharing_config")],
 # let-bound mint after the program clone (program let, then mint let)
 'm_let2': [(CPI + "a.pump_fees.to_account_info(),", "let program=a.pump_fees.to_account_info();let mint_ai=a.mint.to_account_info();" + CPI + "program,"),
            ("mint:a.mint.to_account_info(),sharing_config", "mint:mint_ai,sharing_config")],
 # let-bound event authority (k226 analogue)
 'ea_let': [(CPI, "let ea=a.pump_fees_event_authority.to_account_info();" + CPI), ("event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees", "event_authority:ea,program:a.pump_fees")],
 # let-bound sharing_config clone (o221 analogue)
 'sc_let': [(CPI, "let sc=a.sharing_config.to_account_info();" + CPI), ("sharing_config:a.sharing_config.to_account_info(),event_authority", "sharing_config:sc,event_authority")],
 # mint taken from a by-value helper argument (accounts literal in an inline(always) helper, mint passed last)
 'm_helper': [(CPI + "a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()},signer_seeds),val)?;",
               "#[inline(always)]fn sc_accs<'i>(a:&AdminCto<'i>,mint:AccountInfo<'i>)->crate::pump_fees::cpi::accounts::AdminCtoSharingConfig<'i>{crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint,sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()}}" + CPI + "a.pump_fees.to_account_info(),sc_accs(a,a.mint.to_account_info()),signer_seeds),val)?;")],
 # curve stores: holder before cashback
 'hr_first': [("  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;", "  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;")],
 # late re-read of one plain field through the built CpiContext (w13a21 mx_cpi_* form, applied to sharing_config / event_authority)
 'scx_own': [(CPI, "let mut cpi=CpiContext::new_with_signer("), ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.sharing_config.owner=a.sharing_config.owner;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
 'eax_key': [(CPI, "let mut cpi=CpiContext::new_with_signer("), ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.event_authority.key=a.pump_fees_event_authority.key;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
}
crate = Path(sys.argv[1]); f = crate / 'src/creator/admin_cto.rs'; s = f.read_text(); n0 = s.count('\n')
for g in [g for g in sys.argv[2].split(',') if g]:
    for old, new in G[g]:
        c = s.count(old)
        if c != 1: sys.exit(f'gene {g}: anchor count {c}: {old[:80]}')
        s = s.replace(old, new)
assert s.count('\n') == n0, 'line count changed'
f.write_text(s); print('ok', sys.argv[2])
