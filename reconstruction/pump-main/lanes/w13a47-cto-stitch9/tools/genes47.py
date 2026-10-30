# w13a47-cto-stitch9 gene library keyed on main 52c0b087c. Every gene keeps the newline count.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genes30 as g30, knobs34 as k34
G = dict(g30.G)
for k, v in k34.K.items():
    G.setdefault(k, v)

def apply(names, src):
    s = src
    for n in names:
        for a, b in G[n]:
            c = s.count(a)
            if c != 1:
                raise ValueError(f'gene {n}: pattern count {c}: {a[:90]!r}')
            s = s.replace(a, b)
    if s.count('\n') != src.count('\n'):
        raise ValueError(f'genes {names}: newline count changed')
    return s

# w13a19 o_ab_late: execute's emit_cpi! hand-expanded, authority_bump read after ix
_EM = "emit!(e);emit_cpi!(e);Ok(())"
G['o_ab_late'] = [(_EM, "emit!(e);{let authority_info=ctx.accounts.event_authority.to_account_info();let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);let authority_bump=ctx.bumps.event_authority;anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
G['o_ab_early'] = [(_EM, "emit!(e);{let authority_info=ctx.accounts.event_authority.to_account_info();let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
# w13a19 s_rent_local
G['s_rent_local'] = [("if native{let min=Rent::get()?.minimum_balance(0);", "if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);")]
# w13a19 ph: pool CPI holder from the local (+32 B)
G['ph'] = [("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;", "signer_seeds),target,holder,fee)?;")]
# w13a24-3 k2: holder-rewards PDA before `shared`
_HK = "let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
_SH = "let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};"
G['k2'] = [(_SH + _HK, _HK + _SH)]
# w13a09 sweep transfer-CPI program let (current main's literal clone)
_TFX = "{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}"
G['w_tf_prog2'] = [("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(" + _TFX + ",", "else if !a.coin_creator_vault_ata.data_is_empty(){let program=" + _TFX + ";crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")]
G['w_tf_prog_tti'] = [("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(" + _TFX + ",", "else if !a.coin_creator_vault_ata.data_is_empty(){let program=a.pump_amm.to_account_info();crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")]
# pool_args_pre variants (w13a34 pool_args_pre binds (target,curve.is_holder_reward,fee) after pool_updated)
_PU = "let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();"
_PC1 = "},signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;"
G['pap_b'] = [(_PU, "let pargs=(target,a.bonding_curve.is_holder_reward,fee);" + _PU), (_PC1, "},signer_seeds),pargs.0,pargs.1,pargs.2)?;")]
G['pap_hr'] = [(_PU, _PU + "let phr=a.bonding_curve.is_holder_reward;"), (_PC1, "},signer_seeds),target,phr,fee)?;")]
G['pap_hr_b'] = [(_PU, "let phr=a.bonding_curve.is_holder_reward;" + _PU), (_PC1, "},signer_seeds),target,phr,fee)?;")]
G['pap_destr'] = [(_PU, _PU + "let (ptarget,phr,pfee)=(target,a.bonding_curve.is_holder_reward,fee);"), (_PC1, "},signer_seeds),ptarget,phr,pfee)?;")]
G['pap_th'] = [(_PU, _PU + "let pargs=(target,a.bonding_curve.is_holder_reward);"), (_PC1, "},signer_seeds),pargs.0,pargs.1,fee)?;")]
