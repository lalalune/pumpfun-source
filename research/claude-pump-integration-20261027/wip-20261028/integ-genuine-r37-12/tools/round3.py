#!/usr/bin/env python3
"""round3.py <crate dir>: round-3 lane deliveries (all based on r37g4) and pump-hi patches, re-applied on the
integ-layout composite AFTER the coordfiles / coordlib / nearmiss2 genuine steps (some target code those steps moved).
  pump-hi  anchor-lang feature `allow-missing-optionals` (Cargo.toml): missing trailing optional accounts become None,
           so DistributeFeeToHolders::try_accounts builds AccountNotEnoughKeys only twice (orig 0xc5650).
  bodyloB-04 (cumulative, +7 on r37g4): transfer helpers with the original parameter shapes, wired to the original callers'
           counterparts.  The legacy buy / sell hunks are applied to BOTH copies of the legacy bodies: buy.rs's generic
           `execute` (still used by buy_exact_sol_in) and the lib.rs `buy` / `sell` #[program] handlers that coordlib's
           changes4.py inlined (same statements, path-qualified there).
             0x56658 migrate_v2::refund_pool_authority seeds as one nested temporary passed to an inlined closure
             0x8c2d8/0x8e908/0x90e60/0x91690/0x92820/0x93898: user_quote_payments::transfer_native_unchecked /
             transfer_native_curve_unchecked (lib.rs), collect_v2::transfer_vault_tokens / transfer_user_tokens_ref /
             transfer_user_quote_tokens (collect_creator_fee.rs), token_transfers::transfer_curve_tokens_ref
             (v2_token_transfers.rs), and their call sites (legacy buy/sell, trade_v3 buyback quote transfers, admin_cto
             pay_token).
  bodyloB-05/06: legacy sell SOL output through trade::quote_payments::transfer_native_unchecked<&Signer> (0x95f38 in
           bodyloB's tree; here 0x95f38 is already matched by nearmiss2's move_native, the helper is added as bodyloB has
           it).  bodyloB-06's inline signer seeds in transfer_to_owned/user/recipient are the nearmiss2-07 change that
           nm2_r37.py already makes (0x96d48 / 0x970f8 / 0x97580), so that part is not repeated.
  pump-hi e0864cf19 (claude/pump-hi-20261027, source-on-r37g4.patch, new parts in migrate_v2.rs; the
           required_quote_account_len rewrite is already in r37g5): MigrateV2 is #[event_cpi] (generated owned
           event_authority / program fields replace the explicit UncheckedAccount pair, original struct layout), the
           bonding_curve constraint in the original evaluation order, three combined field lines split one per line
           (migrate_v2.rs line count kept) -> 0xd5af0 MigrateV2::try_accounts, 0x12ba48 __global::migrate_v2.
           body-only/buy_quote-on-r37L2.patch: fee_cpi::buy_quote computes the u128 numerator first, then the
           denominator by u128 checked_sub; with that 0xa0070 differs only in its Source coordinates (lib.rs:2428/2430),
           so buy_quote is MOVED into lib.rs (before reserved_bonding_curve_fees: the original's bonding-curve math region
           2428..2562; fee_cpi.rs, not an original file, re-exports it) and tools/cl/patterns.json pins its two sites.
  bodyloB-07: distribution::sharing_config_shareholders(&AccountInfo) -> Result<Option<Vec<Shareholder>>> (empty data ->
           None, decode failure -> None) used for the TradeEvent shareholders of buy_v2 / sell_v2 (orig 0x8b970); the buy_v2
           statement exists twice here (coordfiles split buy_v2 into its two handlers), both are converted.
  libnear3-02 (cumulative; its GlobalConfig part is in r37g5): migrate / migrate_v2 close the pool-authority token
           accounts through token_2022::close_account helpers (0x48710, 0x54f30, 0x55630) and read the pool-authority
           base ATA through pool_authority_mint_token_account (0x47d00, 0x54c90).
"""
import re, sys
from pathlib import Path
C = Path(sys.argv[1]); S = C / 'src'


def rd(p): return (S / p).read_text()
def wr(p, t): (S / p).write_text(t)


def rep(t, old, new, n=1, what=''):
    assert t.count(old) == n, (what or old[:80], t.count(old), n)
    return t.replace(old, new)


# ---------------------------------------------------------------- pump-hi: anchor-lang allow-missing-optionals
ct = (C / 'Cargo.toml').read_text()
ct = rep(ct, 'anchor-lang = {version = "=0.31.1", features = ["event-cpi", "init-if-needed"]}',
         'anchor-lang = {version = "=0.31.1", features = ["event-cpi", "init-if-needed", "allow-missing-optionals"]}', what='Cargo.toml anchor-lang')
(C / 'Cargo.toml').write_text(ct)

# ---------------------------------------------------------------- bodyloB-04
# migrate_v2 refund_pool_authority (bodyloB-01)
t = rd('migrate_v2.rs')
t = rep(t, " let mint=a.base_mint.key();let bump=[bump];let signer_seeds:&[&[&[u8]];1]=&[&[b\"pool-authority\",mint.as_ref(),&bump]];\n"
           " crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds)\n",
           " let transfer=|signer_seeds:&[&[&[u8]];1]|crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds);\n"
           " transfer(&[&[b\"pool-authority\",a.base_mint.key().as_ref(),&[bump]]])\n", what='refund_pool_authority')
wr('migrate_v2.rs', t)

# helpers: lib.rs user_quote_payments
t = rd('lib.rs')
t = rep(t, "    #[inline(never)]\n    pub fn transfer_from_user<'info>(\n",
        "    #[inline(never)]\n"
        "    pub fn transfer_native_unchecked<'info>(\n"
        "        system_program: &AccountInfo<'info>,\n"
        "        payer: &Signer<'info>,\n"
        "        destination: &AccountInfo<'info>,\n"
        "        amount: u64,\n"
        "    ) -> Result<()> {\n"
        "        anchor_lang::system_program::transfer(\n"
        "            CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {\n"
        "                from: payer.to_account_info(),\n"
        "                to: destination.clone(),\n"
        "            }), amount,\n"
        "        )\n"
        "    }\n"
        "\n"
        "    #[inline(never)]\n"
        "    pub fn transfer_native_curve_unchecked<'info>(\n"
        "        system_program: &AccountInfo<'info>,\n"
        "        payer: &Signer<'info>,\n"
        "        destination: &Account<'info, BondingCurve>,\n"
        "        amount: u64,\n"
        "    ) -> Result<()> {\n"
        "        anchor_lang::system_program::transfer(\n"
        "            CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {\n"
        "                from: payer.to_account_info(),\n"
        "                to: destination.to_account_info(),\n"
        "            }), amount,\n"
        "        )\n"
        "    }\n"
        "\n"
        "    #[inline(never)]\n    pub fn transfer_from_user<'info>(\n", what='user_quote_payments helpers')
wr('lib.rs', t)

# helpers: collect_creator_fee.rs (collect_v2)
t = rd('creator/collect_creator_fee.rs').rstrip('\n') + '\n'
t += '''
#[inline(never)]
pub fn transfer_vault_tokens<'info>(
 token_program:&Interface<'info,anchor_spl::token_interface::TokenInterface>,
 source:&UncheckedAccount<'info>,destination:&UncheckedAccount<'info>,authority:&AccountInfo<'info>,
 decimals:u8,mint:&AccountInfo<'info>,amount:u64,signer_seeds:&[&[&[u8]];1],
)->Result<()>{
 anchor_spl::token_interface::transfer_checked(
  CpiContext::new_with_signer(token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{
   from:source.to_account_info(),to:destination.to_account_info(),authority:authority.clone(),mint:mint.clone(),
  },signer_seeds),amount,decimals,
 )
}

#[inline(never)]
pub fn transfer_user_tokens_ref<'info>(
 token_program:&Interface<'info,anchor_spl::token_interface::TokenInterface>,
 source:&InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,
 destination:&InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,
 authority:&&Signer<'info>,decimals:u8,mint:&AccountInfo<'info>,amount:u64,
)->Result<()>{
 anchor_spl::token_interface::transfer_checked(
  CpiContext::new(token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{
   from:source.to_account_info(),to:destination.to_account_info(),authority:authority.to_account_info(),mint:mint.clone(),
  }),amount,decimals,
 )
}

#[inline(never)]
pub fn transfer_user_quote_tokens<'info>(
 token_program:&Interface<'info,anchor_spl::token_interface::TokenInterface>,
 source:&UncheckedAccount<'info>,destination:&UncheckedAccount<'info>,authority:&AccountInfo<'info>,
 decimals:u8,mint:&AccountInfo<'info>,amount:u64,
)->Result<()>{
 if amount==0{return Ok(());}
 anchor_spl::token_interface::transfer_checked(
  CpiContext::new(token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{
   from:source.to_account_info(),to:destination.to_account_info(),authority:authority.clone(),mint:mint.clone(),
  }),amount,decimals,
 )
}
'''
wr('creator/collect_creator_fee.rs', t)

# helper: v2_token_transfers.rs
t = rd('v2_token_transfers.rs').rstrip('\n') + '\n'
t += '''
/// Transfer curve tokens with the curve authority passed by double reference.
#[inline(never)]
pub fn transfer_curve_tokens_ref<'info>(
    token_program: &Interface<'info, TokenInterface>,
    source: &InterfaceAccount<'info, TokenAccount>,
    destination: &InterfaceAccount<'info, TokenAccount>,
    authority: &&Account<'info, BondingCurve>,
    decimals: u8,
    mint: &AccountInfo<'info>,
    amount: u64,
    signer_seeds: &[&[&[u8]]; 1],
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            token_program.to_account_info(),
            TransferChecked {
                from: source.to_account_info(),
                to: destination.to_account_info(),
                authority: authority.to_account_info(),
                mint: mint.clone(),
            },
            signer_seeds,
        ),
        amount,
        decimals,
    )
}
'''
wr('v2_token_transfers.rs', t)
t = rd('buy_v2.rs')
if '\nmod token_transfers;' in t:
    t = t.replace('\nmod token_transfers;', '\npub mod token_transfers;', 1)
assert '\npub mod token_transfers;' in t
wr('buy_v2.rs', t)

# legacy buy call sites: buy.rs generic body (`token_interface::` / `TransferChecked`) and the lib.rs buy handler
# (changes4: `anchor_spl::token_interface::` paths); same statements.
BUY = [
    (r"if amount>0\{(?:anchor_spl::)?token_interface::transfer_checked\(CpiContext::new_with_signer\(a\.token_program\.to_account_info\(\),(?:anchor_spl::token_interface::)?TransferChecked\{from:a\.associated_bonding_curve\.to_account_info\(\),mint:a\.mint\.to_account_info\(\),to:a\.associated_user\.to_account_info\(\),authority:a\.bonding_curve\.to_account_info\(\)\},&\[seeds\]\),amount,a\.mint\.decimals\)\?;\}",
     "crate::buy_v2::token_transfers::transfer_curve_tokens_ref(&a.token_program,&a.associated_bonding_curve,&a.associated_user,&&a.bonding_curve,a.mint.decimals,a.mint.as_ref(),amount,&[seeds])?;"),
    (r"if quote>0\{anchor_lang::system_program::transfer\(CpiContext::new\(a\.system_program\.to_account_info\(\),anchor_lang::system_program::Transfer\{from:a\.user\.to_account_info\(\),to:a\.bonding_curve\.to_account_info\(\)\}\),quote\)\?;\}",
     "if quote>0{crate::user_quote_payments::transfer_native_curve_unchecked(a.system_program.as_ref(),&a.user,&a.bonding_curve,quote)?;}"),
    (r"for \(to,amount\) in \[\(bb\.clone\(\),bf\),\(a\.fee_recipient\.to_account_info\(\),protocol_fee\)\]\{if amount>0\{anchor_lang::system_program::transfer\(CpiContext::new\(a\.system_program\.to_account_info\(\),anchor_lang::system_program::Transfer\{from:a\.user\.to_account_info\(\),to\}\),amount\)\?;\}\}",
     "if bf>0{crate::user_quote_payments::transfer_native_unchecked(a.system_program.as_ref(),&a.user,bb,bf)?;}\n"
     " if protocol_fee>0{anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to:a.fee_recipient.to_account_info()}),protocol_fee)?;}"),
]
SELL = [
    (r"(?:anchor_spl::)?token_interface::transfer_checked\(CpiContext::new\(a\.token_program\.to_account_info\(\),(?:anchor_spl::token_interface::)?TransferChecked\{from:a\.associated_user\.to_account_info\(\),mint:a\.mint\.to_account_info\(\),to:a\.associated_bonding_curve\.to_account_info\(\),authority:a\.user\.to_account_info\(\)\}\),amount,a\.mint\.decimals\)\?;",
     "crate::collect_v2::transfer_user_tokens_ref(&a.token_program,&a.associated_user,&a.associated_bonding_curve,&&a.user,a.mint.decimals,a.mint.as_ref(),amount)?;"),
]
counts = {}
for f in ['buy.rs', 'lib.rs', 'sell.rs']:
    t = rd(f)
    for i, (pat, new) in enumerate(BUY + SELL):
        indent_new = new
        def sub(m):
            # keep the line's own indentation for the second statement of the bf/protocol split
            line_start = t.rfind('\n', 0, m.start()) + 1
            ind = re.match(r'[ \t]*', t[line_start:]).group(0)
            return indent_new.replace('\n ', '\n' + ind)
        t, n = re.subn(pat, sub, t)
        counts[(f, i)] = n
    wr(f, t)
by = {i: sum(n for (f, j), n in counts.items() if j == i) for i in range(len(BUY) + len(SELL))}
# 3 buy statements x 2 copies (buy.rs execute + lib.rs buy handler); the sell transfer: lib.rs sell handler (+ sell.rs if kept)
assert by[0] == by[1] == by[2] == 2, counts
assert by[3] >= 1, counts

# trade_v3 buyback quote transfers (buy / buy_exact_quote)
t = rd('trade_v3.rs')
t = rep(t, "      if total_buyback!=0 {\n"
           "        token_interface::transfer_checked(CpiContext::new(a.quote_token_program.to_account_info(),TransferChecked{from:a.associated_quote_user.to_account_info(),mint:a.quote_mint.to_account_info(),to:a.buyback_fee_recipient.to_account_info(),authority:a.user.to_account_info()}),total_buyback,decimals)?;\n"
           "      }\n",
           "      crate::collect_v2::transfer_user_quote_tokens(&a.quote_token_program,&a.associated_quote_user,&a.buyback_fee_recipient,a.user.as_ref(),decimals,a.quote_mint.as_ref().as_ref(),total_buyback)?;\n",
           n=2, what='trade_v3 buyback transfers')
wr('trade_v3.rs', t)

# admin_cto pay_token
t = rd('creator/admin_cto.rs')
t = rep(t, "pay_token(a,&a.holder_creator_vault.to_account_info(),&a.holder_creator_vault_quote_token_account.to_account_info(),amount,vaultseeds)?;",
        "pay_token(a,&a.holder_creator_vault.to_account_info(),&a.holder_creator_vault_quote_token_account,amount,vaultseeds)?;", what='pay_token caller')
t = rep(t, "#[inline(never)]fn pay_token<'info>(a:&AdminCto<'info>,owner:&AccountInfo<'info>,to:&AccountInfo<'info>,amount:u64,seeds:&[&[u8]])->Result<()>{\n"
           " anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:to.clone(),",
        "#[inline(never)]fn pay_token<'info>(a:&AdminCto<'info>,owner:&AccountInfo<'info>,to:&UncheckedAccount<'info>,amount:u64,seeds:&[&[u8]])->Result<()>{\n"
        " anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:to.to_account_info(),",
        what='pay_token signature')
t = rep(t, " if amount>0{anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{from:a.creator_vault_quote_token_account.to_account_info(),mint:a.quote_mint.to_account_info(),to:to.clone(),authority:a.creator_vault.to_account_info()},&[seeds]),amount,a.quote_mint.decimals)?;}Ok(())}",
        " if amount>0{crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,to,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&[seeds])?;}Ok(())}",
        what='pay_token transfer')
wr('creator/admin_cto.rs', t)
# ---------------------------------------------------------------- bodyloB-05: legacy sell user output
t = rd('curve_quote_payments.rs').rstrip('\n') + '\n'
t += """
#[inline(never)]
pub fn transfer_native_unchecked<'info,T:AsRef<AccountInfo<'info>>>(
    source:&Account<'info,BondingCurve>,destination:T,amount:u64,
)->Result<()>{
    source.sub_lamports(amount)?;
    destination.add_lamports(amount)?;
    Ok(())
}
"""
wr('curve_quote_payments.rs', t)
n = 0
for f in ['lib.rs', 'sell.rs']:
    t = rd(f); c = t.count("if output!=0 {a.bonding_curve.sub_lamports(output)?;a.user.add_lamports(output)?;}")
    if c:
        t = t.replace("if output!=0 {a.bonding_curve.sub_lamports(output)?;a.user.add_lamports(output)?;}",
                      "if output!=0 {crate::trade::quote_payments::transfer_native_unchecked(&a.bonding_curve,&a.user,output)?;}")
        wr(f, t); n += c
assert n == 1, n

# ---------------------------------------------------------------- libnear3-02: migrate / migrate_v2 close + ATA reader helpers
t = rd('migrate.rs')
lines = t.split('\n')
k = [i for i, l in enumerate(lines) if l.startswith(' if base>0{let mut transfer=vec![12];') and 'call(&base_tok,' in l]
assert len(k) == 1, k
lines[k[0]] = lines[k[0]] + 'let base=pool_authority_mint_token_account(a)?.amount;'
t = '\n'.join(lines)
t = rep(t, "call(&t22,&[(&ulp,false,true),(&wa,false,true),(&pa,true,false)],vec![9],&[pas])?;",
        "close_pool_authority_account(a,ctx.bumps.pool_authority,&a.user_pool_token_account)?;", what='migrate lp close')
t = t.rstrip('\n') + '\n' + """
pub fn close_pool_authority_account<'info>(a:&Migrate<'info>,bump:u8,account:&AccountInfo<'info>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}

fn close_token_account<'info>(a:&Migrate<'info>,account:&AccountInfo<'info>,signer_seeds:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(a.token_2022_program.to_account_info(),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}

#[inline(never)]
pub fn pool_authority_mint_token_account(a:&Migrate)->Result<TokenAccount>{
 let data=a.pool_authority_mint_account.try_borrow_data()?;
 TokenAccount::try_deserialize_unchecked(&mut &data[..])
}
"""
wr('migrate.rs', t)
t = rd('migrate_v2.rs')
t = rep(t, " let base=amount(&tmpb)?;let quote=quote_amount(&tmpq)?.checked_sub(quote_before)",
        " let base=pool_authority_mint_token_account(a)?.amount;let quote=quote_amount(&tmpq)?.checked_sub(quote_before)", what='migrate_v2 base reader')
t = rep(t, " call(&tok,&[(&tmpb,false,true),(&wa,false,true),(&pa,true,false)],vec![9],&[pas])?;\n",
        " close_pool_authority_account(a,ctx.bumps.pool_authority,&a.pool_authority_mint_account,&a.base_token_program)?;\n", what='migrate_v2 base close')
t = rep(t, " call(&qt,&[(&tmpq,false,true),(&wa,false,true),(&pa,true,false)],vec![9],&[pas])?;}\n",
        " close_pool_authority_account(a,ctx.bumps.pool_authority,&a.pool_authority_quote_account,&a.quote_token_program)?;}\n", what='migrate_v2 quote close')
t = rep(t, "call(&t22,&[(&ulp,false,true),(&wa,false,true),(&pa,true,false)],vec![9],&[pas])?;",
        "close_lp_account(a,ctx.bumps.pool_authority,&a.user_pool_token_account)?;", what='migrate_v2 lp close')
t = t.rstrip('\n') + '\n' + """
#[inline(never)]
pub fn pool_authority_mint_token_account(a:&MigrateV2)->Result<TokenAccount>{
 let data=a.pool_authority_mint_account.try_borrow_data()?;
 TokenAccount::try_deserialize_unchecked(&mut &data[..])
}

pub fn close_pool_authority_account<'info>(a:&MigrateV2<'info>,bump:u8,account:&AccountInfo<'info>,token_program:&Interface<'info,TokenInterface>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]],token_program)
}

pub fn close_lp_account<'info>(a:&MigrateV2<'info>,bump:u8,account:&AccountInfo<'info>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]],&a.token_2022_program)
}

#[inline(always)]
fn close_token_account<'info>(a:&MigrateV2<'info>,account:&AccountInfo<'info>,signer_seeds:&[&[&[u8]]],token_program:&AccountInfo<'info>)->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(token_program.clone(),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}
"""
wr('migrate_v2.rs', t)
# ---------------------------------------------------------------- bodyloB-07: sharing_config_shareholders
t = rd('distribution.rs').rstrip('\n') + '\n'
t += """
/// Shareholders of an optional fee-sharing config; empty or undecodable data reads as none.
#[inline(never)]
pub fn sharing_config_shareholders(account:&AccountInfo)->Result<Option<Vec<Shareholder>>>{
 if account.data_is_empty(){return Ok(None);}
 let data=account.try_borrow_data()?;
 match SharingConfig::try_deserialize(&mut &data[..]){Ok(config)=>Ok(Some(config.shareholders)),Err(_)=>Ok(None)}
}
"""
wr('distribution.rs', t)
SH_OLD = "let shareholders={let d=a.sharing_config.try_borrow_data()?;crate::SharingConfig::try_deserialize(&mut &d[..]).map(|s|s.shareholders).unwrap_or_default()};"
SH_NEW = "let shareholders=crate::distribution::sharing_config_shareholders(&a.sharing_config)?.unwrap_or_default();"
nb = rd('buy_v2.rs').count(SH_OLD); ns = rd('sell_v2.rs').count(SH_OLD)
assert nb == 2 and ns == 1, (nb, ns)
wr('buy_v2.rs', rd('buy_v2.rs').replace(SH_OLD, SH_NEW)); wr('sell_v2.rs', rd('sell_v2.rs').replace(SH_OLD, SH_NEW))
# ---------------------------------------------------------------- pump-hi e0864cf19: MigrateV2 accounts struct
t = rd('migrate_v2.rs')
n0 = t.count('\n')
t = rep(t, "#[derive(Accounts)]\npub struct MigrateV2<'info>{", "#[event_cpi]\n#[derive(Accounts)]\npub struct MigrateV2<'info>{", what='MigrateV2 event_cpi')
t = rep(t, "constraint=(if bonding_curve.quote_mint==Pubkey::default(){quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID}else{quote_mint.key()==bonding_curve.quote_mint}) @ PumpError::MintDoesNotMatchBondingCurve)",
        "constraint=quote_mint.key()==bonding_curve.quote_mint||(bonding_curve.quote_mint==Pubkey::default()&&quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)", what='MigrateV2 constraint order')
t = rep(t, " pub system_program:Program<'info,System>,pub pump_amm:Program<'info,admin_cto::Amm>,\n",
        " pub system_program:Program<'info,System>,\n pub pump_amm:Program<'info,admin_cto::Amm>,\n", what='split system/pump_amm')
t = rep(t, " pub base_token_program:Interface<'info,TokenInterface>,pub quote_token_program:Interface<'info,TokenInterface>,\n"
           " pub token_2022_program:Program<'info,Token2022>,pub associated_token_program:Program<'info,AssociatedToken>,\n",
        " pub base_token_program:Interface<'info,TokenInterface>,\n pub quote_token_program:Interface<'info,TokenInterface>,\n"
        " pub token_2022_program:Program<'info,Token2022>,\n pub associated_token_program:Program<'info,AssociatedToken>,\n", what='split programs')
t = rep(t, " /// CHECK: canonical event PDA.\n #[account(seeds=[b\"__event_authority\"],bump)]pub event_authority:UncheckedAccount<'info>,\n"
           " /// CHECK: forwarded event CPI program account.\n pub program:UncheckedAccount<'info>,\n}", "}", what='drop explicit event pair')
assert t.count('\n') == n0, (t.count('\n'), n0)
wr('migrate_v2.rs', t)

# ---------------------------------------------------------------- pump-hi body-only: buy_quote (moved into lib.rs)
f = rd('fee_cpi.rs')
old_bq = ("/// Checked normal-buy quote calculation precedes the fee CPI.\n"
          "pub fn buy_quote(curve: &BondingCurve, amount: u64) -> Result<u128> {\n"
          "    let denominator = curve.virtual_token_reserves.checked_sub(amount)\n"
          "        .ok_or_else(|| error!(crate::PumpError::Overflow))?;\n"
          "    require!(denominator != 0, crate::PumpError::DivisionByZero);\n"
          "    Ok(u128::from(amount) * u128::from(curve.virtual_quote_reserves)\n"
          "        / u128::from(denominator) + 1)\n"
          "}\n")
f = rep(f, old_bq, "// buy_quote lives in lib.rs (the original's bonding-curve math region); re-exported for the legacy callers.\npub use crate::buy_quote;\n", what='fee_cpi buy_quote')
wr('fee_cpi.rs', f)
t = rd('lib.rs')
t = rep(t, "#[inline(never)]\npub fn reserved_bonding_curve_fees(",
        "/// Checked normal-buy quote calculation precedes the fee CPI.\n"
        "pub fn buy_quote(curve: &trade_types::BondingCurve, amount: u64) -> Result<u128> {\n"
        "    let numerator = u128::from(amount) * u128::from(curve.virtual_quote_reserves);\n"
        "    let denominator = u128::from(curve.virtual_token_reserves).checked_sub(u128::from(amount))\n"
        "        .ok_or_else(|| error!(crate::PumpError::Overflow))?;\n"
        "    require!(denominator != 0, crate::PumpError::DivisionByZero);\n"
        "    Ok(numerator / denominator + 1)\n"
        "}\n\n"
        "#[inline(never)]\npub fn reserved_bonding_curve_fees(", what='lib.rs buy_quote')
assert t.count(".ok_or_else(|| error!(crate::PumpError::Overflow))?;") == 1 and t.count("require!(denominator != 0, crate::PumpError::DivisionByZero);") == 1
wr('lib.rs', t)
print('round3 applied: pump-hi allow-missing-optionals, bodyloB-04', {f'{f}#{i}': n for (f, i), n in counts.items() if n})
