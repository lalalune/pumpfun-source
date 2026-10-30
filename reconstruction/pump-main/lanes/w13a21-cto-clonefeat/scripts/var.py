#!/usr/bin/env python3
"""var.py <crate_copy> <gene>[,<gene>...]: apply named source genes (exact string replacements) to a crate copy's
admin_cto.rs. Every gene must apply exactly once (count checked). Line count is preserved (checked)."""
import sys
from pathlib import Path
G = {
 'none': [],
 # cashback evaluated at the curve store (llc oracle: sink of the cashback `and` to bb34 = +0.0024 at 27,400 B)
 'cb_late': [("let holder=holder==Some(true);let cashback=st.cashback&&!holder;", "let holder=holder==Some(true);"),
             ("(holder,cashback,target,sharing_update,collect_old,skip)={", "(holder,target,sharing_update,collect_old,skip)={"),
             ("(holder,cashback,target,sharing_update,collect_old,skip)};", "(holder,target,sharing_update,collect_old,skip)};"),
             ("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=st.cashback&&!holder;")],
 'cb_late3': [("let cashback=st.cashback&&!holder;", "let cashback=st.cashback;"),
              ("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=cashback&&!holder;")],
 'cb_late4': [("let cashback=st.cashback&&!holder;", "let cashback=st.cashback;"),
              ("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=!holder&&cashback;")],
 'cb_late5': [("let cashback=st.cashback&&!holder;", "let cashback=(st.cashback,!holder);"),
              ("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=cashback.0&&cashback.1;")],
 'cb_late6': [("let cashback=st.cashback&&!holder;", "let cashback=(!holder,st.cashback);"),
              ("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=cashback.1&&cashback.0;")],
 'k_bump': [("let bump=[ctx.bumps.creator_vault];", "let bump=ctx.bumps.creator_vault;"), ("old.as_ref(),&bump];", "old.as_ref(),&[bump]];")],
 'k_tfprog': [("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(a.pump_amm.to_account_info(),",
               "else if !a.coin_creator_vault_ata.data_is_empty(){let program=a.pump_amm.to_account_info();crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")],
 'k_iflet': [(" match sharing_update{Some(val)=>{", " if let Some(val)=sharing_update{"), (" }None=>{}}", " }")],
 'k_shprog': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),",
               "let program=a.pump_fees.to_account_info();crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(program,")],
 'k_poolnot': [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")],
 'mx_cpi_is_signer': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(", "let mut cpi=CpiContext::new_with_signer("),
            ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.mint.is_signer=a.mint.is_signer;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
 'mx_cpi_owner': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(", "let mut cpi=CpiContext::new_with_signer("),
            ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.mint.owner=a.mint.owner;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
 'mx_cpi_executable': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(", "let mut cpi=CpiContext::new_with_signer("),
            ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.mint.executable=a.mint.executable;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
 'mx_cpi_rent_epoch': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(", "let mut cpi=CpiContext::new_with_signer("),
            ("signer_seeds),val)?;", "signer_seeds);cpi.accounts.mint.rent_epoch=a.mint.rent_epoch;crate::pump_fees::cpi::admin_cto_sharing_config(cpi,val)?;")],
 'mx_accs_is_signer': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{",
                       "let program=a.pump_fees.to_account_info();let mut accs=crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{"),
            ("program:a.pump_fees.to_account_info()},signer_seeds),val)?;", "program:a.pump_fees.to_account_info()};accs.mint.is_signer=a.mint.is_signer;crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(program,accs,signer_seeds),val)?;")],
 'mx_accs_executable': [("crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{",
                       "let program=a.pump_fees.to_account_info();let mut accs=crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{"),
            ("program:a.pump_fees.to_account_info()},signer_seeds),val)?;", "program:a.pump_fees.to_account_info()};accs.mint.executable=a.mint.executable;crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(program,accs,signer_seeds),val)?;")],
 'pool_hlocal': [("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;","signer_seeds),target,holder,fee)?;")],
 'ev_reset_local': [(" let signer_seeds:&[&[&[u8]]]="," let reset=sharing_update.is_some();let signer_seeds:&[&[&[u8]]]="),("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:reset,")],
 'ev_hr_curve2': [("is_holder_reward:holder,","is_holder_reward:a.bonding_curve.is_holder_reward,")],
 'sk_inline': [("let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&a.sharing_config.key())?;")],
 'w_clock_local': [("     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,", "     let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp:ts,")],
 'cb_late2': [("curve.is_cashback_coin=cashback;", "curve.is_cashback_coin=st.cashback&&!holder;"),
              ("let cashback=st.cashback&&!holder;", "let _cashback=st.cashback&&!holder;"),
              ("(holder,cashback,target,sharing_update,collect_old,skip)};", "(holder,_cashback,target,sharing_update,collect_old,skip)};")],
}
def _lit(x):
    return f"AccountInfo{{lamports:{x}.lamports.clone(),data:{x}.data.clone(),key:{x}.key,owner:{x}.owner,rent_epoch:{x}.rent_epoch,is_signer:{x}.is_signer,is_writable:{x}.is_writable,executable:{x}.executable}}"
_SH = {'pool_authority':'a.pool_authority','authority':'a.admin_set_creator_authority','global':'a.global','mint':'a.mint','sharing_config':'a.sharing_config','event_authority':'a.pump_fees_event_authority','program':'a.pump_fees'}
_SHTXT = "pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()}"
for _f, _x in _SH.items():
    # sharing-CPI account cloned by a hand-written AccountInfo literal with the key read after both Rc clones (keyscan.py oracle)
    G['ki_' + _f] = [(_SHTXT, _SHTXT.replace(f"{_f}:{_x}.to_account_info()", f"{_f}:" + _lit(_x)))]

_KI = "fn ki<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}"
_SHCALL = "signer_seeds),val)?;"
for _f, _x in _SH.items():
    # same clone order, key read last, through a reference binding (one load of the account pointer)
    def _kr(s, _f=_f, _x=_x):
        i = s.index('crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{'); j = s.index('signer_seeds),val)?;', i)
        seg = s[i:j]; old = f"{_f}:{_x}.to_account_info()"
        if seg.count(old) != 1: sys.exit(f'kr_{_f}: anchor')
        return s[:i] + seg.replace(old, f"{_f}:{{let x=&*{_x};" + _lit('x') + "}") + s[j:]
    G['kr_' + _f] = _kr
    # through a nested helper fn taking &AccountInfo (noalias param, like the derived Clone)
    G['kf_' + _f] = [(_SHTXT, _SHTXT.replace(f"{_f}:{_x}.to_account_info()", f"{_f}:ki(&{_x})")), (_SHCALL, _SHCALL + _KI)]

# sweep transfer_creator_fees_to_pump_v2 accounts: field -> source expression (hand-written clone, key after both Rc clones)
_TF = {'system_program':'a.system_program','quote_mint':'a.quote_mint','token_program':'a.quote_token_program','payer':'a.admin_set_creator_authority',
       'associated_token_program':'a.associated_token_program','coin_creator':'a.current_creator','coin_creator_vault_authority':'a.coin_creator_vault_authority',
       'coin_creator_vault_ata':'a.coin_creator_vault_ata','pump_creator_vault':'a.creator_vault','pump_creator_vault_ata':'a.creator_vault_quote_token_account',
       'event_authority':'a.pump_amm_event_authority','program':'a.pump_amm'}
for _f, _x in _TF.items():
    def _tr(s, _f=_f, _x=_x):
        i = s.index('crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{'); j = s.index('}))?;}', i)
        seg = s[i:j]; old = f"{_f}:{_x}.to_account_info()"
        if seg.count(old) != 1: sys.exit(f'tr_{_f}: anchor')
        ref = f"AsRef::<AccountInfo>::as_ref(&*{_x})" if _f == 'quote_mint' else f"&*{_x}"
        return s[:i] + seg.replace(old, f"{_f}:{{let x:&AccountInfo={ref};" + _lit('x') + "}") + s[j:]
    G['tr_' + _f] = _tr

crate = Path(sys.argv[1]); f = crate / 'src/creator/admin_cto.rs'; s = f.read_text(); n0 = s.count('\n')
import subprocess
for g in [g for g in sys.argv[2].split(',') if g]:
    if g.startswith('@'):   # whole admin_cto.rs from another branch (e.g. @w13a22-cto-valslot)
        s = subprocess.run(['git', '-C', str(Path(__file__).resolve().parents[5]), 'show', f'origin/swarm/{g[1:]}:programs/pump/src/creator/admin_cto.rs'], capture_output=True, text=True, check=True).stdout
        continue
    if g.startswith('tf:') or g.startswith('sh:'):
        # tf:<field>:<order> / sh:<field>:<order>: hand-written AccountInfo clone of that CPI account with the literal's
        # fields in <order> (k key, l lamports, d data, o owner, r rent_epoch, s is_signer, w is_writable, e executable)
        _, fld, order = g.split(':')
        if g.startswith('tf:'):
            x = _TF[fld]; i = s.index('crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{'); j = s.index('}))?;}', i)
        else:
            x = _SH[fld]; i = s.index('crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{'); j = s.index('signer_seeds),val)?;', i)
        F = {'k': 'key:x.key', 'l': 'lamports:x.lamports.clone()', 'd': 'data:x.data.clone()', 'o': 'owner:x.owner', 'r': 'rent_epoch:x.rent_epoch',
             's': 'is_signer:x.is_signer', 'w': 'is_writable:x.is_writable', 'e': 'executable:x.executable'}
        assert sorted(order) == sorted('kldorswe'), order
        ref = f"AsRef::<AccountInfo>::as_ref(&*{x})" if fld == 'quote_mint' else f"&*{x}"
        seg = s[i:j]; old = f"{fld}:{x}.to_account_info()"
        if seg.count(old) != 1: sys.exit(f'{g}: anchor')
        s = s[:i] + seg.replace(old, f"{fld}:{{let x:&AccountInfo={ref};AccountInfo{{" + ','.join(F[c] for c in order) + "}}") + s[j:]
        continue
    if callable(G[g]):
        s = G[g](s); continue
    for old, new in G[g]:
        c = s.count(old)
        if c != 1: sys.exit(f'gene {g}: anchor count {c}: {old[:80]}')
        s = s.replace(old, new)
assert s.count('\n') == n0, 'line count changed'
f.write_text(s); print('ok', sys.argv[2])
