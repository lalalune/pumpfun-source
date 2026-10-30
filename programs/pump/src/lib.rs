#[path="admin_set_idl_authority.rs"]pub mod idl_authority;#[path="buy.rs"]pub mod legacy_buy;pub mod buy_v2;
pub use buy_v2::*;
pub mod create_v2;
pub use create_v2::*;
#[path="creator/admin_cto.rs"]pub mod admin_cto;
pub use admin_cto::*;
pub mod creator{#[path="collect_creator_fee.rs"]pub mod collect_creator_fee;}pub use creator::collect_creator_fee as collect_v2;
pub use collect_v2::*;
#[path="creator/distribute_creator_fees.rs"]pub mod distribution;
pub use distribution::*;
pub use distribution::minimum;
pub use minimum::*;
#[path="creator/distribute_fee_to_holders.rs"]pub mod holder_distribution;
pub use holder_distribution::*;
#[path="creator/migrate_bonding_curve_creator.rs"]pub mod creator_migration;
pub use creator_migration::*;
#[path="creator/set_creator.rs"]pub mod set_creator;#[path="creator/set_metaplex_creator.rs"]pub mod set_metaplex_creator;
pub use set_creator::*;pub use set_metaplex_creator::*;
#[path="v2_native_payments.rs"]pub mod v2_native_payments;#[path="legacy_native_payments.rs"]pub mod legacy_native_payments;
pub use legacy_buy::*;
#[path="extend_account.rs"]pub mod extend;#[path = "fee_recipient.rs"] pub(crate) mod fee_recipient;pub mod mayhem_virtual_params;
pub use extend::*;
pub mod migrate;
pub use migrate::*;
pub mod migrate_v2;
pub use migrate_v2::*;
#[path="multi_hop_curve_swap.rs"]pub mod multi_hop_curve;
pub use multi_hop_curve::*;
#[path="pump_quote.rs"]pub mod pump_quote;
pub mod quote_control;
pub use quote_control::*;
#[path="sell.rs"]pub mod legacy_sell;
pub use legacy_sell::*;
pub mod sell_v2;
pub use sell_v2::*;
pub mod set_reserved_fee_recipients;
#[path="sweep_fees.rs"]pub mod sweep;
pub use sweep::*;
pub mod incentives;
pub use incentives::*;
pub mod token_incentives;
pub use token_incentives::*;
pub use token_incentives::volume_accumulator::{GlobalVolumeAccumulator, UserVolumeAccumulator};
pub use token_incentives::volume_sync;
pub use volume_sync::*;
#[path = "trade_v3.rs"] pub mod trade;
pub use trade::*;
#[path="util/constant_product.rs"] pub mod constant_product; #[path="util/fee.rs"] pub mod fee_math;#[path="util/payments.rs"] pub mod payments;
#[path="util/transfer_fee.rs"] pub mod transfer_fee_recovered;#[path="util/withheld.rs"] pub mod withheld;#[path="curve_quote_payments.rs"] pub mod quote_payments;#[path="util/user_payments.rs"] pub mod user_payments;
pub mod global_init;
pub use global_init::*;
pub mod cashback;
pub use cashback::*;
pub mod create;
pub use create::*;
pub mod set_params;
pub use set_params::*;

pub use idl_authority::*;

pub use mayhem_virtual_params::*;


use anchor_lang::prelude::*;




// layout-pad: aligns the next Source site with the original lib.rs line












declare_id!("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P");
declare_program!(pump_amm);
declare_program!(pump_fees);
declare_program!(mayhem);


// layout-pad: aligns the next Source site with the original lib.rs line

#[program]
pub mod pump_recovered {
    use super::*;
    pub fn initialize(ctx:Context<Initialize>)->Result<()>{global_init::execute(ctx)}
    pub fn update_global_authority(ctx:Context<UpdateGlobalAuthority>)->Result<()>{update_global_authority_handler(ctx)}
// layout-pad: aligns the next Source site with the original lib.rs line

















    pub fn toggle_create_v2(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.create_v2_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.create_v2_enabled = enabled;
        Ok(())
    }
// layout-pad: aligns the next Source site with the original lib.rs line

    pub fn toggle_cashback_enabled(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.is_cashback_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.is_cashback_enabled = enabled;
        Ok(())
    }
    pub fn update_holder_reward_config(ctx:Context<AdminGlobal>,is_holder_reward_enabled:bool,holder_reward_claim_authority:Pubkey)->Result<()>{ctx.accounts.global.is_holder_reward_enabled=is_holder_reward_enabled;ctx.accounts.global.holder_reward_claim_authority=holder_reward_claim_authority;Ok(())}
    pub fn set_max_curve_depth(ctx: Context<AdminGlobal>, max_curve_depth: u8) -> Result<()> {
        ctx.accounts.global.max_curve_depth = max_curve_depth;
        Ok(())
    }
// layout-pad: aligns the next Source site with the original lib.rs line

















    pub fn toggle_mayhem_mode(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.mayhem_mode_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.mayhem_mode_enabled = enabled;
        Ok(())
    }
    pub fn update_creator_fee_config(ctx:Context<AdminGlobal>,creator_fee_configurable:bool,max_configurable_creator_fee_bps:u64)->Result<()>{
      ctx.accounts.global.creator_fee_configurable=creator_fee_configurable;ctx.accounts.global.max_configurable_creator_fee_bps=max_configurable_creator_fee_bps;
      let event=UpdateCreatorFeeConfigEvent{timestamp:Clock::get()?.unix_timestamp,authority:ctx.accounts.authority.key(),creator_fee_configurable,max_configurable_creator_fee_bps};emit!(event);emit_cpi!(event);Ok(())
    }
    pub fn add_quote_mint(ctx:Context<AdminGlobal>,quote_mint:Pubkey)->Result<()>{ctx.accounts.global.add_quote_mint(quote_mint)}
    pub fn remove_quote_mint(ctx:Context<AdminGlobal>,quote_mint:Pubkey)->Result<()>{ctx.accounts.global.remove_quote_mint(quote_mint)}
    pub fn set_virtual_quote_reserves(ctx:Context<AdminGlobal>,initial_virtual_quote_reserves:u64)->Result<()>{ctx.accounts.global.initial_virtual_quote_reserves=initial_virtual_quote_reserves;Ok(())}
    pub fn set_params(mut ctx:Context<SetParams>,initial_virtual_token_reserves:u64,initial_virtual_sol_reserves:u64,initial_real_token_reserves:u64,token_total_supply:u64,fee_basis_points:u64,withdraw_authority:Pubkey,enable_migrate:bool,pool_migration_fee:u64,creator_fee_basis_points:u64,set_creator_authority:Pubkey,admin_set_creator_authority:Pubkey)->Result<()>{
     let recipients=crate::legacy_sell::fee_recipient::set_fee_recipients(&mut ctx)?;



// layout-pad: aligns the next Source site with the original lib.rs line
























































     require_gt!(token_total_supply,initial_real_token_reserves,PumpError::InitialRealTokenReservesShouldBeLessThanTokenTotalSupply);
// layout-pad: aligns the next Source site with the original lib.rs line




     require_gt!(initial_virtual_token_reserves,initial_real_token_reserves,PumpError::InitialVirtualTokenReservesShouldBeGreaterThanInitialRealTokenReserves);
// layout-pad: aligns the next Source site with the original lib.rs line
     ctx.accounts.global.initial_virtual_token_reserves=initial_virtual_token_reserves;ctx.accounts.global.initial_real_token_reserves=initial_real_token_reserves;ctx.accounts.global.initial_virtual_sol_reserves=initial_virtual_sol_reserves;ctx.accounts.global.token_total_supply=token_total_supply;











     require_gte!(1000u64,fee_basis_points,PumpError::FeeBasisPointsGreaterThanMaximum);
// layout-pad: aligns the next Source site with the original lib.rs line
     ctx.accounts.global.fee_basis_points=fee_basis_points;




     require_keys_neq!(withdraw_authority,anchor_lang::system_program::ID,PumpError::AllZerosWithdrawAuthority);
     ctx.accounts.global.withdraw_authority=withdraw_authority;ctx.accounts.global.enable_migrate=enable_migrate;
// layout-pad: aligns the next Source site with the original lib.rs line
















     let final_real_sol_reserves=u64::try_from((initial_real_token_reserves as u128).checked_mul(initial_virtual_sol_reserves as u128).and_then(move|v|v.checked_div((initial_virtual_token_reserves-initial_real_token_reserves) as u128)).ok_or_else(||error!(PumpError::Overflow))?).map_err(|_|error!(PumpError::Truncation))?;
// layout-pad: aligns the next Source site with the original lib.rs line
     require_gt!(final_real_sol_reserves,pool_migration_fee,PumpError::PoolMigrationFeeShouldBeLessThanFinalRealSolReserves);
// layout-pad: aligns the next Source site with the original lib.rs line
     ctx.accounts.global.pool_migration_fee=pool_migration_fee;





     require_gte!(1000u64,creator_fee_basis_points,PumpError::FeeBasisPointsGreaterThanMaximum);
     let g=&mut ctx.accounts.global;g.creator_fee_basis_points=creator_fee_basis_points;g.set_creator_authority=set_creator_authority;g.admin_set_creator_authority=admin_set_creator_authority;












     let event=SetParamsEvent{initial_virtual_token_reserves,initial_virtual_sol_reserves,initial_real_token_reserves,token_total_supply,fee_basis_points,withdraw_authority,enable_migrate,pool_migration_fee,creator_fee_basis_points,set_creator_authority,admin_set_creator_authority,final_real_sol_reserves,fee_recipients:recipients,timestamp:Clock::get()?.unix_timestamp};emit!(event);emit_cpi!(event);Ok(())
    }
    pub fn set_mayhem_virtual_params(ctx: Context<SetMayhemVirtualParams>) -> Result<()> { mayhem_virtual_params::execute(ctx) }
    pub fn set_reserved_fee_recipients(ctx:Context<AdminReadonly>,whitelist_pda:Pubkey)->Result<()>{crate::set_reserved_fee_recipients::set_reserved_fee_recipients(ctx,whitelist_pda)





    }
// layout-pad: aligns the next Source site with the original lib.rs line






























    pub fn create(ctx:Context<Create>,name:String,symbol:String,uri:String,creator:Pubkey)->Result<()>{
     require_keys_neq!(creator,Pubkey::default(),PumpError::CreatorShouldNotBeZero);
     {let a=&mut *ctx.accounts;let curve:&mut trade_types::BondingCurve=&mut a.bonding_curve;let g=&a.global;let quote_mint=Pubkey::default();let virtual_quote_reserves=if quote_mint==Pubkey::default(){g.initial_virtual_sol_reserves}else{g.initial_virtual_quote_reserves};curve.virtual_quote_reserves=virtual_quote_reserves;curve.initial_virtual_quote_reserves=virtual_quote_reserves;curve.virtual_token_reserves=g.initial_virtual_token_reserves;curve.real_token_reserves=g.initial_real_token_reserves;curve.real_quote_reserves=0;curve.token_total_supply=g.token_total_supply;curve.creator=creator;curve.quote_mint=quote_mint;curve.post_complete_base_out=0;curve.creator_fee_bps=0;curve.post_complete_quote_in=0;curve.depth=0;curve.is_mayhem_mode=false;curve.is_cashback_coin=false;curve.can_edit_creator_fee=false;curve.is_holder_reward=false;}let a=&ctx.accounts;
     create_metadata(&ctx,&name,&symbol,&uri,creator)?;
     mint_tokens(a,&a.mint,&a.associated_bonding_curve,ctx.bumps.mint_authority)?;
     revoke_mint_authority(ctx.bumps.mint_authority,&(&a.token_program,&a.mint,&a.mint_authority))?;
     let event=create_event(name,symbol,uri,creator,&a.mint,&a.user,&a.bonding_curve,&a.token_program,false,0)?;
     
     emit!(event);emit_cpi!(event);Ok(())
    }
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
    pub fn create_v2<'info>(ctx:Context<'_,'_,'_,'info,CreateV2<'info>>,name:String,symbol:String,uri:String,creator:Pubkey,is_mayhem_mode:bool,is_cashback_enabled:OptionBool,creator_fee_bps:CreationOptionU64,is_holder_reward:OptionBool)->Result<()>{create_v2::execute(ctx,name,symbol,uri,creator,is_mayhem_mode,is_cashback_enabled,creator_fee_bps,is_holder_reward)}
    #[inline(never)] pub fn buy_v2<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,amount:u64,max_sol_cost:u64,partial_fill:OptionBool)->Result<()>{buy_v2::execute(ctx,amount,max_sol_cost,partial_fill.0,false)}
    #[inline(never)] pub fn buy_exact_quote_in_v2<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:OptionBool)->Result<()>{buy_v2::execute(ctx,spendable_quote_in,min_tokens_out,partial_fill.0,true)}
    #[inline(never)]pub fn sell_v2(ctx:Context<SellV2>,amount:u64,min_sol_output:u64)->Result<()>{sell_v2::execute(ctx,amount,min_sol_output)}
    #[inline(never)]pub fn buy_v3(ctx: Context<SellV3>, amount:u64,max_sol_cost:u64,partial_fill:OptionBool)->Result<()>{trade::buy(ctx,amount,max_sol_cost,partial_fill.0)}
    #[inline(never)]pub fn buy_exact_quote_in_v3(ctx:Context<SellV3>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:OptionBool)->Result<()>{trade::buy_exact_quote(ctx,spendable_quote_in,min_tokens_out,partial_fill.0)}
    #[inline(never)]pub fn sell_v3(ctx: Context<SellV3>, amount: u64, min_sol_output: u64) -> Result<()> { trade::sell(ctx, amount, min_sol_output) }
    pub fn multi_hop_curve_swap<'info>(ctx:Context<'_,'_,'info,'info,MultiHopCurve<'info>>,amount_in:u64,hop_fees:Vec<u8>)->Result<CurveRunResult>{multi_hop_curve::execute(ctx,amount_in,hop_fees)}
    pub fn sweep_protocol_fee(ctx:Context<SweepFees>)->Result<()>{sweep::execute(ctx,false)}
    pub fn sweep_creator_fee(ctx:Context<SweepFees>)->Result<()>{sweep::execute(ctx,true)}
    pub fn buy<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,amount:u64,max_sol_cost:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{
     let fee_recipient=&ctx.accounts.fee_recipient;
     let bonding_curve=&mut ctx.accounts.bonding_curve;let (associated_bonding_curve,associated_user,token_program)=(&ctx.accounts.associated_bonding_curve,&ctx.accounts.associated_user,&ctx.accounts.token_program);
     crate::trade_types::prepare_bonding_curve(bonding_curve,&ctx.accounts.system_program,&ctx.accounts.user)?;
     crate::legacy_sell::fee_recipient::validate_fee_recipient(fee_recipient,&ctx.accounts.global,bonding_curve)?;
     let buyback_fee_recipient=crate::legacy_sell::buyback_fee_recipient(ctx.remaining_accounts,&ctx.accounts.global,1)?;
// layout-pad: aligns the next Source site with the original lib.rs line

















































































































































































































































     require!(!bonding_curve.complete,PumpError::BondingCurveComplete);
// layout-pad: aligns the next Source site with the original lib.rs line


     let amount=if partial_fill.0{amount.min(bonding_curve.real_token_reserves)}else{amount};
// layout-pad: aligns the next Source site with the original lib.rs line



     require_gt!(amount,0,PumpError::BuyZeroAmount);

     require_gte!(bonding_curve.real_token_reserves,amount,PumpError::NotEnoughTokensToBuy);
// layout-pad: aligns the next Source site with the original lib.rs line








     let sol_cost=u64::try_from(crate::legacy_sell::fee_cpi::buy_quote(bonding_curve,amount)?).map_err(|_|error!(PumpError::Truncation))?;
     let (protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps)={let fees=crate::legacy_sell::fee_cpi::trade_fees(
      &ctx.accounts.global,bonding_curve,&ctx.accounts.mint,&ctx.accounts.fee_config,&ctx.accounts.fee_program,ctx.accounts.program.as_ref(),sol_cost
     )?;if ctx.accounts.global.whitelist_pda==ctx.accounts.user.key(){(0,0,0,0)}else{fees}};
// layout-pad: aligns the next Source site with the original lib.rs line




















     require_gte!(max_sol_cost,
// layout-pad: aligns the next Source site with the original lib.rs line








      sol_cost.checked_add(protocol_fee).ok_or_else(||error!(PumpError::Overflow))?

      .checked_add(creator_fee).ok_or_else(||error!(PumpError::Overflow))?,
      PumpError::TooMuchSolRequired);
// layout-pad: aligns the next Source site with the original lib.rs line





     bonding_curve.virtual_token_reserves=bonding_curve.virtual_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.real_token_reserves=bonding_curve.real_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.virtual_quote_reserves=bonding_curve.virtual_quote_reserves.checked_add(sol_cost).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.real_quote_reserves=bonding_curve.real_quote_reserves.checked_add(sol_cost).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line

     let transfer=|signer_seeds:&[&[&[u8]];1]|crate::buy_v2::token_transfers::transfer_curve_tokens_ref(token_program,associated_bonding_curve,associated_user,&bonding_curve,ctx.accounts.mint.decimals,ctx.accounts.mint.as_ref(),amount,signer_seeds);transfer(&[&[b"bonding-curve",ctx.accounts.mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])?;
// layout-pad: aligns the next Source site with the original lib.rs line








     if ctx.accounts.user.key()==ctx.accounts.global.whitelist_pda{
      ctx.accounts.associated_bonding_curve.reload()?;
      ctx.accounts.associated_user.reload()?;
      let quote_mint=bonding_curve.quote_mint;
      bonding_curve.sync_virtual_quote_reserves(ctx.accounts.associated_bonding_curve.amount,ctx.accounts.associated_user.amount,&quote_mint)?;
     }
// layout-pad: aligns the next Source site with the original lib.rs line







     if ctx.accounts.user_volume_accumulator.user==Pubkey::default(){ctx.accounts.user_volume_accumulator.user=ctx.accounts.user.key();}
// layout-pad: aligns the next Source site with the original lib.rs line












     let mint=ctx.accounts.mint.key();
     let mut cashback=false;
     if creator_fee!=0{
      crate::legacy_sell::check_bonding_curve_v2(ctx.remaining_accounts,&mint.key())?;
      if bonding_curve.is_cashback_coin{
       #[inline(always)] fn pay_owned<'info>(to:AccountInfo<'info>,system_program:&AccountInfo<'info>,user:&Signer<'info>,amount:u64)->Result<()>{crate::user_quote_payments::transfer_native_owned(system_program,user,to,amount)}
       pay_owned(ctx.accounts.user_volume_accumulator.to_account_info(),ctx.accounts.system_program.as_ref(),&ctx.accounts.user,creator_fee)?;
// layout-pad: aligns the next Source site with the original lib.rs line









       ctx.accounts.user_volume_accumulator.cashback_earned=ctx.accounts.user_volume_accumulator.cashback_earned.checked_add(creator_fee).ok_or(error!(PumpError::Overflow))?;
       cashback=true;
      }else{
       crate::legacy_buy::native_payments::ensure_rent_exempt(&ctx.accounts.system_program,&ctx.accounts.user,&ctx.accounts.creator_vault)?;
       crate::user_quote_payments::transfer_native_unchecked(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&ctx.accounts.creator_vault,creator_fee)?;
      }
     }
     crate::user_quote_payments::transfer_native_curve(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&bonding_curve,sol_cost)?;
     let mut buyback_fee=0;
     if protocol_fee!=0{
      let (fee,remaining)=crate::buy_v2::recipient_payments::split_protocol_fee(&ctx.accounts.global,protocol_fee,bonding_curve.is_mayhem_mode);
      if fee!=0{crate::user_quote_payments::transfer_native_curve_unchecked(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&buyback_fee_recipient,fee)?;}
      crate::user_quote_payments::transfer_native_recipient(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&fee_recipient,remaining)?;
      buyback_fee=fee;
     }
     let virtual_token_reserves=bonding_curve.virtual_token_reserves;
     let virtual_quote_reserves=bonding_curve.virtual_quote_reserves;
     let real_token_reserves=bonding_curve.real_token_reserves;
     let real_quote_reserves=bonding_curve.real_quote_reserves;
     let creator=bonding_curve.creator;
     let timestamp=Clock::get()?.unix_timestamp;
     let event=crate::trade_types::TradeEvent{
      total_unclaimed_tokens:ctx.accounts.user_volume_accumulator.total_unclaimed_tokens,
      total_claimed_tokens:ctx.accounts.user_volume_accumulator.total_claimed_tokens,
      current_sol_volume:ctx.accounts.user_volume_accumulator.current_sol_volume,
      last_update_timestamp:ctx.accounts.user_volume_accumulator.last_update_timestamp,
      mint,
      sol_amount:sol_cost,
      token_amount:amount,
      is_buy:true,
      user:ctx.accounts.user.key(),
      timestamp,
      virtual_sol_reserves:virtual_quote_reserves,
      virtual_token_reserves,
      real_sol_reserves:real_quote_reserves,
      real_token_reserves,
      fee_recipient:fee_recipient.key(),
      fee_basis_points:protocol_fee_bps,
      fee:protocol_fee,
      creator,
      creator_fee_basis_points:if cashback{0}else{creator_fee_bps},
      creator_fee:if cashback{0}else{creator_fee},
      track_volume:track_volume.0,
      holder_rewards_bps:if bonding_curve.is_holder_reward{creator_fee_bps}else{0},
      holder_rewards:if bonding_curve.is_holder_reward{creator_fee}else{0},
      ix_name:"buy".to_string(),
      mayhem_mode:bonding_curve.is_mayhem_mode,
      cashback_fee_basis_points:if cashback{creator_fee_bps}else{0},
      cashback:if cashback{creator_fee}else{0},
      buyback_fee_basis_points:if bonding_curve.is_mayhem_mode{0}else{ctx.accounts.global.buyback_basis_points},
      buyback_fee,
      shareholders:vec![],
      quote_mint:bonding_curve.quote_mint,
      quote_amount:sol_cost,
      virtual_quote_reserves,
      real_quote_reserves,
      creator_fee_unclaimed:bonding_curve.creator_fee,
      unparsed_trailing_field:0,
     };
     emit!(event);
     emit_cpi!(event);
     if ctx.accounts.bonding_curve.real_token_reserves==0{
      ctx.accounts.bonding_curve.complete=true;
      let event=crate::trade_types::CompleteEvent{user:ctx.accounts.user.key(),mint,bonding_curve:ctx.accounts.bonding_curve.key(),timestamp,quote_mint:ctx.accounts.bonding_curve.quote_mint};
      emit!(event);
      emit_cpi!(event);
     }
     Ok(())
    }
    pub fn buy_exact_sol_in<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,spendable_sol_in:u64,min_tokens_out:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{legacy_buy::buy_exact_sol_in(ctx,spendable_sol_in,min_tokens_out,track_volume,partial_fill)}
    pub fn sell<'info>(ctx:Context<'_,'_,'info,'info,LegacySell<'info>>,amount:u64,min_sol_output:u64)->Result<()>{let minimum=min_sol_output;
     let fee_recipient=&ctx.accounts.fee_recipient;let user=&ctx.accounts.user;
     let bonding_curve=&mut ctx.accounts.bonding_curve;let (associated_bonding_curve,associated_user,token_program)=(&ctx.accounts.associated_bonding_curve,&ctx.accounts.associated_user,&ctx.accounts.token_program);
     crate::trade_types::prepare_bonding_curve(bonding_curve,&ctx.accounts.system_program,user)?;
     crate::legacy_sell::fee_recipient::validate_fee_recipient(fee_recipient,&ctx.accounts.global,bonding_curve)?;

// layout-pad: aligns the next Source site with the original lib.rs line
















































































































































     require!(!bonding_curve.complete,PumpError::BondingCurveComplete);
// layout-pad: aligns the next Source site with the original lib.rs line
     require_gt!(amount,0,PumpError::SellZeroAmount);
// layout-pad: aligns the next Source site with the original lib.rs line
     require_gte!(ctx.accounts.associated_user.amount,amount,PumpError::NotEnoughTokensToSell);
// layout-pad: aligns the next Source site with the original lib.rs line







     let sol_output=u64::try_from(bonding_curve.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;
     let (protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps)={let fees=crate::legacy_sell::fee_cpi::trade_fees(
      &ctx.accounts.global,bonding_curve,&ctx.accounts.mint,&ctx.accounts.fee_config,&ctx.accounts.fee_program,ctx.accounts.program.as_ref(),sol_output
     )?;if ctx.accounts.global.whitelist_pda==ctx.accounts.user.key(){(0,0,0,0)}else{fees}};
// layout-pad: aligns the next Source site with the original lib.rs line





















     let output=sol_output.checked_sub(protocol_fee).ok_or_else(||error!(PumpError::Overflow))?
// layout-pad: aligns the next Source site with the original lib.rs line
      .checked_sub(creator_fee).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line

     require_gte!(output,min_sol_output,PumpError::TooLittleSolReceived);
// layout-pad: aligns the next Source site with the original lib.rs line








     bonding_curve.virtual_token_reserves=bonding_curve.virtual_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.real_token_reserves=bonding_curve.real_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.virtual_quote_reserves=bonding_curve.virtual_quote_reserves.checked_sub(sol_output).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



     bonding_curve.real_quote_reserves=bonding_curve.real_quote_reserves.checked_sub(sol_output).ok_or_else(||error!(PumpError::Overflow))?;
     crate::collect_v2::transfer_user_tokens_ref(token_program,associated_user,associated_bonding_curve,&user,ctx.accounts.mint.decimals,ctx.accounts.mint.as_ref(),amount)?;
     if ctx.accounts.user.key()==ctx.accounts.global.whitelist_pda{ctx.accounts.associated_bonding_curve.reload()?;ctx.accounts.associated_user.reload()?;let quote_mint=bonding_curve.quote_mint;bonding_curve.sync_virtual_quote_reserves(ctx.accounts.associated_bonding_curve.amount,ctx.accounts.associated_user.amount,&quote_mint)?;}
     let mut cashback=false;let mut index=1;if creator_fee!=0{if bonding_curve.is_cashback_coin{crate::legacy_sell::process_cashback(ctx.remaining_accounts,&ctx.accounts.mint.key(),&ctx.accounts.user,ctx.accounts.system_program.as_ref(),bonding_curve,creator_fee)?;cashback=true;index=2;}else{crate::legacy_sell::check_bonding_curve_v2(ctx.remaining_accounts,&ctx.accounts.mint.key())?;crate::legacy_buy::native_payments::ensure_rent_exempt(&ctx.accounts.system_program,&ctx.accounts.user,&ctx.accounts.creator_vault)?;crate::trade::quote_payments::move_native(bonding_curve,&ctx.accounts.creator_vault,creator_fee)?;}}
     let buyback_fee_recipient=crate::legacy_sell::buyback_fee_recipient(ctx.remaining_accounts,&ctx.accounts.global,index)?;
     crate::trade::quote_payments::transfer_native(bonding_curve,&user,output)?;
     let mut buyback_fee=0;
     if protocol_fee!=0{let (fee,remaining)=crate::buy_v2::recipient_payments::split_protocol_fee(&ctx.accounts.global,protocol_fee,bonding_curve.is_mayhem_mode);if fee!=0{crate::trade::quote_payments::move_native(bonding_curve,&buyback_fee_recipient,fee)?;}crate::trade::quote_payments::transfer_native(bonding_curve,&fee_recipient,remaining)?;buyback_fee=fee;}
     let virtual_token_reserves=bonding_curve.virtual_token_reserves;let virtual_quote_reserves=bonding_curve.virtual_quote_reserves;let real_token_reserves=bonding_curve.real_token_reserves;let real_quote_reserves=bonding_curve.real_quote_reserves;
     let creator=bonding_curve.creator;
     let event=crate::trade_types::TradeEvent{user:ctx.accounts.user.key(),mint:ctx.accounts.mint.key(),timestamp:Clock::get()?.unix_timestamp,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,sol_amount:sol_output,token_amount:amount,is_buy:false,
      virtual_sol_reserves:virtual_quote_reserves,virtual_token_reserves,real_sol_reserves:real_quote_reserves,real_token_reserves,fee_recipient:fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:protocol_fee,creator,creator_fee_basis_points:if cashback{0}else{creator_fee_bps},creator_fee:if cashback{0}else{creator_fee},track_volume:false,
      holder_rewards_bps:if bonding_curve.is_holder_reward{creator_fee_bps}else{0},holder_rewards:if bonding_curve.is_holder_reward{creator_fee}else{0},ix_name:"sell".to_string(),mayhem_mode:bonding_curve.is_mayhem_mode,cashback_fee_basis_points:if cashback{creator_fee_bps}else{0},cashback:if cashback{creator_fee}else{0},
      buyback_fee_basis_points:if bonding_curve.is_mayhem_mode{0}else{ctx.accounts.global.buyback_basis_points},buyback_fee,shareholders:vec![],quote_mint:bonding_curve.quote_mint,quote_amount:sol_output,virtual_quote_reserves,real_quote_reserves,creator_fee_unclaimed:bonding_curve.creator_fee,unparsed_trailing_field:0,};
     emit!(event);emit_cpi!(event);Ok(())
    }
    pub fn migrate<'info>(ctx:Context<'_,'_,'_,'info,Migrate<'info>>)->Result<()>{migrate::execute(ctx)}
    pub fn migrate_v2<'info>(ctx:Context<'_, '_, '_, 'info,MigrateV2<'info>>)->Result<()>{migrate_v2::execute(ctx)}
    pub fn extend_account(ctx:Context<ExtendAccount>)->Result<()>{extend::execute(ctx)}
    pub fn collect_creator_fee(ctx:Context<CollectCreatorFee>)->Result<()>{collect_v2::collect_creator_fee(ctx)









    }
    pub fn collect_creator_fee_v2(ctx:Context<CollectCreatorFeeV2>)->Result<()>{collect_v2::execute(ctx)}
    pub fn distribute_fee_to_holders<'info>(ctx:Context<'_, '_, '_, 'info,DistributeFeeToHolders<'info>>,amounts:Vec<u64>)->Result<()>{holder_distribution::execute(ctx,amounts)}
    pub fn set_metaplex_creator(ctx:Context<SetMetaplexCreator>)->Result<()>{set_metaplex_creator::sync(ctx)}
    pub fn set_creator(ctx:Context<SetCreator>,creator:Pubkey)->Result<()>{set_creator::set(ctx,creator)}
    pub fn admin_cto(ctx:Context<AdminCto>,is_holder_reward:Option<bool>,creator_fee_bps:Option<u64>,new_creator:Option<Pubkey>)->Result<()>{admin_cto::execute(ctx,is_holder_reward,creator_fee_bps,new_creator)}
    pub fn admin_update_token_incentives(ctx: Context<AdminUpdateTokenIncentives>, start_time: i64, end_time: i64, seconds_in_a_day: i64, day_number: u64, pump_token_supply_per_day: u64) -> Result<()> { incentives::execute(ctx, start_time, end_time, seconds_in_a_day, day_number, pump_token_supply_per_day) }
    pub fn claim_token_incentives(ctx: Context<ClaimTokenIncentives>) -> Result<()> { token_incentives::claim(ctx) }
    pub fn claim_cashback(ctx:Context<ClaimCashback>)->Result<()>{cashback::claim(ctx)}
    pub fn claim_cashback_v2(ctx:Context<ClaimCashbackV2>)->Result<()>{cashback::claim_v2(ctx)}
    pub fn init_user_volume_accumulator(ctx:Context<InitUserVolume>)->Result<()>{token_incentives::init_user_volume_accumulator::execute(ctx)}


    pub fn close_user_volume_accumulator(ctx:Context<CloseUserVolume>)->Result<()>{token_incentives::close_user_volume_accumulator::execute(ctx)}


    pub fn sync_user_volume_accumulator(ctx:Context<SyncUserVolumeAccumulator>)->Result<()>{volume_sync::execute(ctx)}
    pub fn admin_set_idl_authority(ctx:Context<AdminSetIdlAuthority>,idl_authority:Pubkey)->Result<()>{idl_authority::execute(ctx,idl_authority)}
    pub fn migrate_bonding_curve_creator(ctx:Context<MigrateBondingCurveCreator>)->Result<()>{creator_migration::execute(ctx)}
    pub fn get_minimum_distributable_fee<'info>(ctx:Context<'_,'_,'_,'info,GetMinimumDistributableFee<'info>>)->Result<MinimumDistributableFeeEvent>{minimum::execute(ctx)}
    pub fn distribute_creator_fees<'info>(ctx:Context<'_,'_,'_,'info,DistributeCreatorFees<'info>>)->Result<DistributeCreatorFeesEvent>{distribution::execute(ctx)}
    pub fn distribute_creator_fees_v2<'info>(ctx:Context<'_,'_,'_,'info,DistributeCreatorFeesV2<'info>>,initialize_ata:bool)->Result<DistributeCreatorFeesEvent>{distribution::execute_v2(ctx,initialize_ata)}
    pub fn update_buyback_config(ctx:Context<AdminGlobal>,buyback_basis_points:Option<u64>)->Result<()>{crate::set_reserved_fee_recipients::update_buyback_config(ctx,buyback_basis_points)






    }
    pub fn initialize_quote_control(ctx: Context<InitializeQuoteControl>) -> Result<()> { quote_control::initialize_quote_control(ctx) }
    pub fn set_quote_control_admin(ctx: Context<SetQuoteControlAdmin>, new_admin: Pubkey) -> Result<()> { quote_control::set_quote_control_admin(ctx, new_admin) }
    pub fn add_quote_control_mint(ctx: Context<UpdateQuoteControlMints>, quote_mint: Pubkey, initial_virtual_quote_reserves: u64) -> Result<()> { quote_control::add_quote_control_mint(ctx, quote_mint, initial_virtual_quote_reserves) }
    pub fn remove_quote_control_mint(ctx: Context<UpdateQuoteControlMints>, quote_mint: Pubkey) -> Result<()> { quote_control::remove_quote_control_mint(ctx, quote_mint) }
    pub fn set_quote_control_reserves_admin(ctx: Context<SetQuoteControlReservesAdmin>, new_reserves_admin: Pubkey) -> Result<()> { quote_control::set_quote_control_reserves_admin(ctx, new_reserves_admin) }
    pub fn set_quote_control_mint_reserves(ctx: Context<SetQuoteControlMintReserves>, quote_mint: Pubkey, initial_virtual_quote_reserves: u64) -> Result<()> { quote_control::set_quote_control_mint_reserves(ctx, quote_mint, initial_virtual_quote_reserves) }
}

#[error_code]
pub enum PumpError {
    #[msg("The given account is not authorized to execute this instruction.")]
    NotAuthorized,
    #[msg("The program is already initialized.")]
    AlreadyInitialized,
    #[msg("slippage: Too much SOL required to buy the given amount of tokens.")]
    TooMuchSolRequired,
    #[msg("slippage: Too little SOL received to sell the given amount of tokens.")]
    TooLittleSolReceived,
    #[msg("The mint does not match the bonding curve.")]
    MintDoesNotMatchBondingCurve,
    #[msg("The bonding curve has completed and liquidity migrated to raydium.")]
    BondingCurveComplete,
    #[msg("The bonding curve has not completed.")]
    BondingCurveNotComplete,
    #[msg("The program is not initialized.")]
    NotInitialized,
    #[msg("Withdraw too frequent")]
    WithdrawTooFrequent,
    #[msg("new_size should be > current_size")]
    NewSizeShouldBeGreaterThanCurrentSize,
    #[msg("Account type not supported")]
    AccountTypeNotSupported,
    #[msg("initial_real_token_reserves should be less than token_total_supply")]
    InitialRealTokenReservesShouldBeLessThanTokenTotalSupply,
    #[msg("initial_virtual_token_reserves should be greater than initial_real_token_reserves")]
    InitialVirtualTokenReservesShouldBeGreaterThanInitialRealTokenReserves,
    #[msg("fee_basis_points greater than maximum")]
    FeeBasisPointsGreaterThanMaximum,
    #[msg("Withdraw authority cannot be set to System Program ID")]
    AllZerosWithdrawAuthority,
    #[msg("pool_migration_fee should be less than final_real_sol_reserves")]
    PoolMigrationFeeShouldBeLessThanFinalRealSolReserves,
    #[msg("pool_migration_fee should be greater than creator_fee + MAX_MIGRATE_FEES")]
    PoolMigrationFeeShouldBeGreaterThanCreatorFeePlusMaxMigrateFees,
    #[msg("Migrate instruction is disabled")]
    DisabledWithdraw,
    #[msg("Migrate instruction is disabled")]
    DisabledMigrate,
    #[msg("Invalid creator pubkey")]
    InvalidCreator,
    #[msg("Buy zero amount")]
    BuyZeroAmount,
    #[msg("Not enough tokens to buy")]
    NotEnoughTokensToBuy,
    #[msg("Sell zero amount")]
    SellZeroAmount,
    #[msg("Not enough tokens to sell")]
    NotEnoughTokensToSell,
    #[msg("Overflow")]
    Overflow,
    #[msg("Truncation")]
    Truncation,
    #[msg("Division by zero")]
    DivisionByZero,
    #[msg("Not enough remaining accounts")]
    NotEnoughRemainingAccounts,
    #[msg("All fee recipients should be non-zero")]
    AllFeeRecipientsShouldBeNonZero,
    #[msg("Unsorted or not unique fee recipients")]
    UnsortedNotUniqueFeeRecipients,
    #[msg("Creator should not be zero")]
    CreatorShouldNotBeZero,
    StartTimeInThePast,
    EndTimeInThePast,
    EndTimeBeforeStartTime,
    TimeRangeTooLarge,
    EndTimeBeforeCurrentDay,
    SupplyUpdateForFinishedRange,
    DayIndexAfterEndIndex,
    DayInActiveRange,
    InvalidIncentiveMint,
    #[msg("Buy: Not enough SOL to cover for rent exemption.")]
    BuyNotEnoughSolToCoverRent,
    #[msg("Buy: Not enough SOL to cover for fees.")]
    BuyNotEnoughSolToCoverFees,
    #[msg("Slippage: Would buy less tokens than expected min_tokens_out")]
    BuySlippageBelowMinTokensOut,
    NameTooLong,
    SymbolTooLong,
    UriTooLong,
    CreateV2Disabled,
    CpitializeMayhemFailed,
    MayhemModeDisabled,
    #[msg("creator has been migrated to sharing config")]
    CreatorMigratedToSharingConfig,
    #[msg("creator_vault has been migrated to sharing config, use pump:distribute_creator_fees instead")]
    UnableToDistributeCreatorVaultMigratedToSharingConfig,
    #[msg("Sharing config is not active")]
    SharingConfigNotActive,
    #[msg("The recipient account is executable, so it cannot receive lamports, remove it from the team first")]
    UnableToDistributeCreatorFeesToExecutableRecipient,
    #[msg("Bonding curve creator does not match sharing config")]
    BondingCurveAndSharingConfigCreatorMismatch,
    #[msg("Remaining accounts do not match shareholders, make sure to pass exactly the same pubkeys in the same order")]
    ShareholdersAndRemainingAccountsMismatch,
    #[msg("Share bps must be greater than 0")]
    InvalidShareBps,
    #[msg("Cashback is not enabled")]
    CashbackNotEnabled,
    #[msg("Buyback fee recipient not authorized")]
    BuybackFeeRecipientNotAuthorized,
    AllBuybackFeeRecipientsShouldBeNonZero,
    NotUniqueBuybackFeeRecipients,
    #[msg("buyback_basis_points must be <= 10_000")]
    BuybackBasisPointsOutOfRange,
    #[msg("buyback fee recipients require exactly 8 remaining accounts (or none)")]
    WrongBuybackFeeRecipientsCount,
    BuybackFeeRecipientMissing,
    #[msg("Unsupported quote mint")]
    UnsupportedQuoteMint,
    #[msg("Create v2: quote token program must be SPL Token or Token-2022")]
    InvalidQuoteTokenProgram,
    #[msg("Create v2: associated quote bonding curve address does not match derivation")]
    InvalidAssociatedQuoteBondingCurve,
    #[msg("Quote mint whitelist is full")]
    QuoteMintWhitelistFull,
    #[msg("Quote mint is already whitelisted")]
    QuoteMintAlreadyWhitelisted,
    #[msg("Quote mint is not in the whitelist")]
    QuoteMintNotWhitelisted,
    #[msg("Quote mint cannot be added or removed via whitelist (default or native SOL mint)")]
    QuoteMintNotEligibleForWhitelist,
    #[msg("Unable to distribute creator fees to uninitialized account")]
    UnableToDistributeCreatorFeesToUninitializedAccount,
    #[msg("Mayhem mode quote mint not allowed")]
    MayhemModeQuoteMintNotAllowed,
    #[msg("Cashback trade is missing the required remaining accounts")]
    MissingCashbackAccounts,
    #[msg("Cashback user_volume_accumulator account is invalid")]
    InvalidCashbackAccumulator,
    #[msg("bonding_curve_v2 remaining account is missing or invalid")]
    InvalidBondingCurveV2,
    #[msg("quote_control remaining account does not match derivation or is uninitialized")]
    InvalidQuoteControl,
    #[msg("Cashback recipient token account is not owned by user")]
    InvalidCashbackRecipient,
    #[msg("Configurable creator fees are disabled")]
    CreatorFeeNotConfigurable,
    #[msg("Creator fee basis points must be between 1 and the configured maximum")]
    CreatorFeeBpsOutOfRange,
    #[msg("Creator fee is not editable for this bonding curve")]
    CreatorFeeNotEditable,
    #[msg("Creator fee cannot be configured for a cashback coin")]
    CreatorFeeNotAllowedForCashbackCoin,
    #[msg("Bonding curve has already migrated")]
    BondingCurveAlreadyMigrated,
    #[msg("Cashback coins can no longer be created")]
    CashbackDeprecated,
    #[msg("The creator of a holder-reward coin cannot be changed")]
    HolderRewardCreatorImmutable,
    #[msg("Holder-reward coins are disabled")]
    HolderRewardDisabled,
    #[msg("Holder-reward amounts and recipient accounts do not match")]
    HolderRewardRecipientsMismatch,
    #[msg("The holder-rewards PDA cannot be left below its rent-exempt minimum")]
    HolderRewardsRentFloor,
    #[msg("A holder-rewards token account is required on a token quote")]
    HolderRewardTokenAccountMissing,
    #[msg("CTO is not allowed on a mayhem-mode coin")]
    CtoNotAllowedForMayhemCoin,
    #[msg("new_creator is required unless converting to holder rewards")]
    CtoNewCreatorRequired,
    #[msg("new_creator must be omitted when converting to holder rewards")]
    CtoNewCreatorNotAllowed,
    #[msg("Creator fee is not configurable on a SOL or whitelisted quote; the fee schedule applies")]
    CreatorFeeNotConfigurableForQuote,
    #[msg("current_creator must be passed writable so the outgoing creator can be paid")]
    CtoCreatorAccountNotWritable,
    #[msg("A frozen sharing-config vault account holds a balance; thaw it before the holder conversion")]
    CtoSharedVaultFrozen,
    #[msg("v3 trades do not support cashback coins; use the v2 instructions")]
    CashbackCoinNotSupported,
    #[msg("creator_fee must be swept before the creator changes or the vault is distributed")]
    CreatorFeesNotSwept,
    #[msg("The fee config tier table is empty")]
    FeeTiersEmpty,
    #[msg("The fee config account is shorter than its initialize size")]
    FeeConfigTooShort,
    #[msg("multi-hop: a hop's input mint is neither side of its bonding curve")]
    MultiHopDiscontinuousPath,
    #[msg("Quote bonding curve remaining account does not match derivation or is uninitialized")]
    InvalidQuoteBondingCurve,
    #[msg("Quote bonding curve is not eligible as a quote: mayhem mode, or the chain's depth-0 root is quoted in a mint no list admits")]
    QuoteBondingCurveNotEligible,
    #[msg("A quote-chain bonding curve has migrated: its pool and vault remaining accounts are required")]
    QuotePoolAccountsRequired,
    #[msg("Quote pool remaining account is not an initialized pump-amm pool")]
    QuotePoolNotFound,
    #[msg("Quote pool or vault remaining accounts do not match derivation or are invalid")]
    InvalidQuotePool,
    #[msg("Derived quote reserves are zero")]
    QuoteReservesOutOfRange,
    #[msg("The new curve's depth (quote coin depth plus one) exceeds Global.max_curve_depth or the program's cap of 5")]
    CurveDepthExceeded,
    #[msg("multi-hop: hop_fees must carry one flag byte per curve hop using only the protocol and creator bits")]
    MultiHopHopFeesMismatch,
    #[msg("A quote-chain coin's curve is complete but not yet migrated; retry once migrate_v2 creates its pool")]
    QuoteCurveAwaitingMigration,
    #[msg("multi-hop: mayhem-mode curves are not routable; use the v2 instructions")]
    MultiHopMayhemCurveNotSupported,
    #[msg("The quote coin is nested: a bonding curve remaining account is required for every coin on its quote chain down to the depth-0 root")]
    QuoteChainAccountsRequired,
    // Binary evidence extends the captured official IDL, which stops at 6109.
    #[msg("quote_mint must be writable for a quote with a Token-2022 transfer fee: its withheld fees are harvested to the mint")]
    QuoteMintNotWritable = 110,
}

// layout-pad: aligns the next Source site with the original lib.rs line





























































































































/// Quote token accounts of a curve-signed quote transfer (both are required when the quote is not native).
#[inline(always)]
pub(crate) fn curve_quote_accounts<'a, 'info>(quote_source: Option<&'a AccountInfo<'info>>, quote_destination: Option<&'a AccountInfo<'info>>) -> (&'a AccountInfo<'info>, &'a AccountInfo<'info>) {
    let source_tokens: &'a AccountInfo<'info> = quote_source.unwrap();
    let to_account = quote_destination.unwrap();
    (source_tokens, to_account)
}




























/// Quote token accounts of a user-signed quote transfer (both are required when the quote is not native).
#[inline(always)]
pub(crate) fn user_quote_accounts<'a, 'info>(quote_source: Option<&'a AccountInfo<'info>>, quote_destination: Option<&'a AccountInfo<'info>>) -> (&'a AccountInfo<'info>, &'a AccountInfo<'info>) {
    let from_account_info = quote_source.unwrap();
    let to_account = quote_destination.unwrap();
    (from_account_info, to_account)
}














































































































































































































































































































































#[account]
pub struct Global {
    pub initialized: bool,
    pub authority: Pubkey,
    pub fee_recipient: Pubkey,
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub fee_basis_points: u64,
    pub withdraw_authority: Pubkey,
    pub enable_migrate: bool,
    pub pool_migration_fee: u64,
    pub creator_fee_basis_points: u64,
    pub fee_recipients: [Pubkey; 7],
    pub set_creator_authority: Pubkey,
    pub admin_set_creator_authority: Pubkey,
    pub create_v2_enabled: bool,
    pub whitelist_pda: Pubkey,
    pub reserved_fee_recipient: Pubkey,
    pub mayhem_mode_enabled: bool,
    pub reserved_fee_recipients: [Pubkey; 7],
    pub is_cashback_enabled: bool,
    pub buyback_fee_recipients: [Pubkey; 8],
    pub buyback_basis_points: u64,
    pub initial_virtual_quote_reserves: u64,
    pub whitelisted_quote_mints: [Pubkey; 1],
    pub creator_fee_configurable: bool,
    pub max_configurable_creator_fee_bps: u64,
    pub holder_reward_claim_authority: Pubkey,
    pub is_holder_reward_enabled: bool,
    pub max_curve_depth: u8,
}

// layout-pad: aligns the next Source site with the original lib.rs line

















impl Global {
 #[inline(never)]
 pub fn set_buyback_basis_points(&mut self,value:u64)->Result<()>{
  require!(value<=10000,PumpError::BuybackBasisPointsOutOfRange);
  self.buyback_basis_points=value;
  Ok(())
 }
// layout-pad: aligns the next Source site with the original lib.rs line


 #[inline(never)]
 pub fn validate_buyback_fee_recipient(&self,buyback_fee_recipient:&Pubkey)->Result<()>{
  require_keys_neq!(*buyback_fee_recipient,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);
// layout-pad: aligns the next Source site with the original lib.rs line



  require!(self.buyback_fee_recipients.contains(buyback_fee_recipient),PumpError::BuybackFeeRecipientNotAuthorized);
  Ok(())
 }
// layout-pad: aligns the next Source site with the original lib.rs line





 #[inline(never)]
 pub fn set_buyback_fee_recipients(&mut self,recipients:[Pubkey;8])->Result<()>{
  require!(recipients.iter().all(|key|*key!=Pubkey::default()),PumpError::AllBuybackFeeRecipientsShouldBeNonZero);
// layout-pad: aligns the next Source site with the original lib.rs line








  for left in 0..8 {for right in left+1..8 {require_neq!(recipients[left],recipients[right],PumpError::NotUniqueBuybackFeeRecipients);}}
  self.buyback_fee_recipients=recipients;
  Ok(())
 }
}

// layout-pad: aligns the next Source site with the original lib.rs line




















/// Buyback / retained split of a protocol fee (no buyback in mayhem mode).
#[inline(always)]
fn protocol_fee_split(buyback_basis_points: u64, protocol_fee: u64, is_mayhem_mode: bool) -> (u64, u64) {
    if is_mayhem_mode { return (0, protocol_fee); } let scaled = buyback_basis_points as u128 * protocol_fee as u128 / 10000;
    let buyback_fee = u64::try_from(scaled).expect("buyback fee is at most protocol_fee");
    let remaining = protocol_fee
        .checked_sub(buyback_fee)
            .expect("buyback_fee never exceeds protocol_fee");
    (buyback_fee, remaining)
}
#[inline(never)]
pub(crate) fn split_protocol_fee(global: &crate::Global, protocol_fee: u64, is_mayhem_mode: bool) -> (u64, u64) {
    protocol_fee_split(global.buyback_basis_points, protocol_fee, is_mayhem_mode)
}


impl Global {
    pub fn add_quote_mint(&mut self,quote_mint:Pubkey)->Result<()>{
     require_keys_neq!(quote_mint,Pubkey::default(),PumpError::QuoteMintNotEligibleForWhitelist);
// layout-pad: aligns the next Source site with the original lib.rs line



     require_keys_neq!(quote_mint,anchor_spl::token::spl_token::native_mint::ID,PumpError::QuoteMintNotEligibleForWhitelist);
// layout-pad: aligns the next Source site with the original lib.rs line



     require_eq!(self.whitelisted_quote_mints.contains(&quote_mint),false,PumpError::QuoteMintAlreadyWhitelisted);
// layout-pad: aligns the next Source site with the original lib.rs line









     for slot in self.whitelisted_quote_mints.iter_mut(){if *slot==Pubkey::default(){*slot=quote_mint;return Ok(());}} err!(PumpError::QuoteMintWhitelistFull)
        }
// layout-pad: aligns the next Source site with the original lib.rs line
    pub fn remove_quote_mint(&mut self,quote_mint:Pubkey)->Result<()>{
     require_keys_neq!(quote_mint,Pubkey::default(),PumpError::QuoteMintNotEligibleForWhitelist);
// layout-pad: aligns the next Source site with the original lib.rs line









     for slot in self.whitelisted_quote_mints.iter_mut(){if *slot==quote_mint{*slot=Pubkey::default();return Ok(());}} err!(PumpError::QuoteMintNotWhitelisted)
        }
}
pub mod trade_types;
/// Checked normal-buy quote calculation precedes the fee CPI.
pub fn buy_quote(curve: &trade_types::BondingCurve, amount: u64) -> Result<u128> {
    let numerator = u128::from(amount) * u128::from(curve.virtual_quote_reserves);
    let denominator = u128::from(curve.virtual_token_reserves).checked_sub(u128::from(amount))
// layout-pad: aligns the next Source site with the original lib.rs line

















































































































































































































































































































































































































































        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line
    require!(denominator != 0, crate::PumpError::DivisionByZero);
    Ok(numerator / denominator + 1)
}

impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn sell_quote(&self,amount:u64)->Result<u128>{
  let numerator=self.virtual_quote_reserves as u128*amount as u128;
// layout-pad: aligns the next Source site with the original lib.rs line















  numerator.checked_div(self.virtual_token_reserves as u128+amount as u128).ok_or_else(||error!(PumpError::DivisionByZero))
 }
}
#[inline(never)] pub fn tokens_for_quote(curve:&crate::trade_types::BondingCurve,quote:u64)->Result<u128>{let effective=quote.checked_sub(1).ok_or(PumpError::Overflow)?;crate::constant_product::output(effective as u128,curve.virtual_quote_reserves as u128,curve.virtual_token_reserves as u128)}
#[inline(never)]
pub(crate) fn buy_fee_market_cap(curve:&trade_types::BondingCurve,mint:&anchor_spl::token_interface::Mint)->Result<u128>{
 let supply=if curve.is_mayhem_mode {curve.token_total_supply}else{mint.supply};
// layout-pad: aligns the next Source site with the original lib.rs line



















 (u128::from(supply)*u128::from(curve.virtual_quote_reserves)).checked_div(u128::from(curve.virtual_token_reserves)).ok_or_else(||error!(PumpError::DivisionByZero))
}

// layout-pad: aligns the next Source site with the original lib.rs line








impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn apply_buy(&mut self,amount:u64,quote:u64)->Result<()>{
  self.virtual_token_reserves=self.virtual_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.real_token_reserves=self.real_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.virtual_quote_reserves=self.virtual_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.real_quote_reserves=self.real_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(())
 }
// layout-pad: aligns the next Source site with the original lib.rs line



 #[inline(never)]
 pub fn apply_sell(&mut self,amount:u64,quote:u64)->Result<()>{
  self.virtual_token_reserves=self.virtual_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.real_token_reserves=self.real_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.virtual_quote_reserves=self.virtual_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line



  self.real_quote_reserves=self.real_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(())
 }
}

impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn accrue_fees(&mut self,global:&Global,protocol_fee:u64,creator_fee:u64)->Result<u64>{
  let (buyback_fee,retained)=protocol_fee_split(global.buyback_basis_points,protocol_fee,self.is_mayhem_mode);



// layout-pad: aligns the next Source site with the original lib.rs line


  self.protocol_fees=self.protocol_fees.checked_add(retained).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad: aligns the next Source site with the original lib.rs line


  self.creator_fee=self.creator_fee.checked_add(creator_fee).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(buyback_fee)
 }
}

#[inline(never)]
pub fn reserved_bonding_curve_fees(curve: &trade_types::BondingCurve) -> Result<u64> {
    curve.creator_fee.checked_add(curve.protocol_fees)
        .ok_or_else(|| error!(crate::PumpError::Overflow))
}

// layout-pad: aligns the next Source site with the original lib.rs line
impl crate::trade_types::BondingCurve {
    // The original handler calls a separate helper at 0xa23f0.
    #[inline(never)]
    pub(crate) fn sync_virtual_quote_reserves(
        &mut self,
        initial_real_token_reserves: u64,
        vault_amount: u64,
        quote_mint: &Pubkey,
    ) -> Result<()> {
        let bc = self;
        if bc.complete || !bc.is_mayhem_mode {
            return Ok(());
        }
        let real_quote_reserves = bc.real_quote_reserves;
        let virtual_token_reserves = bc.virtual_token_reserves;
        let denominator = bc
            .token_total_supply
            .checked_mul(2)
            .ok_or(PumpError::Overflow)?
            .checked_sub(initial_real_token_reserves)
            .ok_or(PumpError::Overflow)?
            .checked_sub(vault_amount)
            .ok_or(PumpError::Overflow)?;
        if *quote_mint == Pubkey::default() {
            if real_quote_reserves < 10_000_000 || denominator < 1_000_000_000_000 {
                return Ok(());
            }
        } else if real_quote_reserves < 1_000_000 || denominator < 1_000_000_000_000 {
            return Ok(());
        }
        // Keep these fallible operations separate: the captured helper has
        // distinct Overflow returns for multiplication and division.
        let numerator = (denominator as u128)
            .checked_add(virtual_token_reserves as u128)
            .ok_or(PumpError::Overflow)?
            .checked_mul(real_quote_reserves as u128)
            .ok_or(PumpError::Overflow)?;
        let computed = numerator
            .checked_div(denominator as u128)
            .ok_or(PumpError::Overflow)?;
        // Conversion precedes the cap in both captured branches.
        if *quote_mint == Pubkey::default() {
            let amount = u64::try_from(computed)?;
            bc.virtual_quote_reserves = amount.min(2_000_000_000_000);
        } else {
            let amount = u64::try_from(computed)?;
            bc.virtual_quote_reserves = amount.min(160_000_000_000);
        }
        Ok(())
    }
}






















#[event]
#[derive(Clone)]
pub struct CreateEvent {pub name:String,pub symbol:String,pub uri:String,pub mint:Pubkey,pub bonding_curve:Pubkey,pub user:Pubkey,pub creator:Pubkey,pub timestamp:i64,pub virtual_token_reserves:u64,pub virtual_sol_reserves:u64,pub real_token_reserves:u64,pub token_total_supply:u64,pub token_program:Pubkey,pub is_mayhem_mode:bool,pub is_cashback_enabled:bool,pub quote_mint:Pubkey,pub virtual_quote_reserves:u64,pub creator_fee_bps:u64,pub is_holder_reward:bool,pub depth:u8}






















#[event]
#[derive(Clone)]
pub struct TradeEvent {
    pub mint: Pubkey,
    pub sol_amount: u64,
    pub token_amount: u64,
    pub is_buy: bool,
    pub user: Pubkey,
    pub timestamp: i64,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub fee_recipient: Pubkey,
    pub fee_basis_points: u64,
    pub fee: u64,
    pub creator: Pubkey,
    pub creator_fee_basis_points: u64,
    pub creator_fee: u64,
    pub track_volume: bool,
    pub total_unclaimed_tokens: u64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
    pub last_update_timestamp: i64,
    pub ix_name: String,
    pub mayhem_mode: bool,
    pub cashback_fee_basis_points: u64,
    pub cashback: u64,
    pub buyback_fee_basis_points: u64,
    pub buyback_fee: u64,
    pub shareholders: Vec<Shareholder>,
    pub quote_mint: Pubkey,
    pub quote_amount: u64,
    pub virtual_quote_reserves: u64,
    pub real_quote_reserves: u64,
    pub holder_rewards_bps: u64,
    pub holder_rewards: u64,
    pub creator_fee_unclaimed: u64,
    pub unparsed_trailing_field: u64,
}

#[event]
#[derive(Clone)]
pub struct CompleteEvent {pub user:Pubkey,pub mint:Pubkey,pub bonding_curve:Pubkey,pub timestamp:i64,pub quote_mint:Pubkey}
#[event]
#[derive(Clone)]pub struct PostCompleteBuyEvent{pub user:Pubkey,pub mint:Pubkey,pub bonding_curve:Pubkey,pub quote_mint:Pubkey,pub timestamp:i64,pub base_out:u64,pub quote_in:u64,pub fee_basis_points:u64,pub fee:u64,pub creator_fee_basis_points:u64,pub creator_fee:u64,pub buyback_fee:u64,pub pool_base_reserves_before:u64,pub pool_quote_reserves_before:u64,pub pool_base_reserves_after:u64,pub pool_quote_reserves_after:u64}
#[event]
#[derive(Clone)]
pub struct SetParamsEvent{pub initial_virtual_token_reserves:u64,pub initial_virtual_sol_reserves:u64,pub initial_real_token_reserves:u64,pub final_real_sol_reserves:u64,pub token_total_supply:u64,pub fee_basis_points:u64,pub withdraw_authority:Pubkey,pub enable_migrate:bool,pub pool_migration_fee:u64,pub creator_fee_basis_points:u64,pub fee_recipients:[Pubkey;8],pub timestamp:i64,pub set_creator_authority:Pubkey,pub admin_set_creator_authority:Pubkey}

































































#[derive(Accounts)]
pub struct Initialize<'info>{
 #[account(init,payer=user,space=1088,seeds=[b"global"],bump)]
 pub global:Account<'info,Global>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
}

// layout-pad: aligns the next Source site with the original lib.rs line
#[event_cpi]
#[derive(Accounts)]
pub struct AdminGlobal<'info> {
    #[account(mut, seeds = [b"global"], bump, has_one = authority @ PumpError::NotAuthorized)]
    pub global: Account<'info, Global>,
    #[account(mut)]
    pub authority: Signer<'info>,
}















pub mod bonding_curve_instruction_accounts{use super::*;#[event_cpi]
#[derive(Accounts)]
pub struct Create<'info>{
 #[account(init,payer=user,mint::decimals=6,mint::authority=mint_authority)]
 pub mint:Box<Account<'info,anchor_spl::token::Mint>>,
 /// CHECK: canonical program mint authority.
 #[account(seeds=[b"mint-authority"],bump)]
 pub mint_authority:UncheckedAccount<'info>,
 #[account(init,payer=user,space=166,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]
 pub bonding_curve:Box<Account<'info,trade_types::BondingCurve>>,
 #[account(init,payer=user,associated_token::mint=mint,associated_token::authority=bonding_curve)]
 pub associated_bonding_curve:Box<Account<'info,anchor_spl::token::TokenAccount>>,
 #[account(seeds=[b"global"],bump)]
 pub global:Account<'info,Global>,
 pub mpl_token_metadata:Program<'info,create::MetadataProgram>,
 /// CHECK: canonical metadata account, allocated by the metadata program.
 #[account(mut,seeds=[b"metadata",anchor_spl::metadata::ID.as_ref(),mint.key().as_ref()],bump,seeds::program=mpl_token_metadata.key())]
 pub metadata:UncheckedAccount<'info>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub token_program:Program<'info,anchor_spl::token::Token>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 pub rent:Sysvar<'info,Rent>,
}

// layout-pad: aligns the next Source site with the original lib.rs line



































#[derive(Accounts)]
pub struct LegacyBuy<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 /// CHECK: handler validates recipient.
 #[account(mut)]pub fee_recipient:UncheckedAccount<'info>,
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Account<'info,trade_types::BondingCurve>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,
 #[account(mut,token::mint=mint)]pub associated_user:InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 /// CHECK: PDA checked.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 /// CHECK: event authority.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: self CPI.
 pub program:Program<'info,crate::program::PumpRecovered>,
 #[account(seeds=[b"global_volume_accumulator"],bump)]pub global_volume_accumulator:Box<Account<'info,crate::GlobalVolumeAccumulator>>,
 #[account(init_if_needed,payer=user,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Box<Account<'info,crate::UserVolumeAccumulator>>,
 /// CHECK: fee program validates config.
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]
 pub fee_config:Account<'info,legacy_sell::LegacyFeeConfig>,
 /// CHECK: canonical dependency.
 pub fee_program:Program<'info,legacy_sell::LegacyFeesProgram>,
}

#[derive(Accounts)]
pub struct LegacySell<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,#[doc="CHECK: handler validates recipient."]#[account(mut)]pub fee_recipient:UncheckedAccount<'info>,pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,#[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Account<'info,trade_types::BondingCurve>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,#[account(mut,token::mint=mint)]pub associated_user:InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,#[account(mut)]pub user:Signer<'info>,pub system_program:Program<'info,System>,#[doc="CHECK: PDA checked."]#[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,pub token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 #[doc="CHECK: event authority."]#[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,#[doc="CHECK: self CPI."]pub program:Program<'info,crate::program::PumpRecovered>,#[doc="CHECK: fee program validates config."]#[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]pub fee_config:Account<'info,legacy_sell::LegacyFeeConfig>,#[doc="CHECK: canonical dependency."]pub fee_program:Program<'info,legacy_sell::LegacyFeesProgram>,
}}pub use bonding_curve_instruction_accounts::*;



#[derive(AnchorSerialize,Clone)]
pub struct OptionBool(pub bool);
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

#[event]
#[derive(Clone)]
pub struct UpdateCreatorFeeConfigEvent {pub timestamp:i64,pub authority:Pubkey,pub creator_fee_configurable:bool,pub max_configurable_creator_fee_bps:u64}

















#[event]
#[derive(Clone)]
pub struct UpdateGlobalAuthorityEvent{pub global:Pubkey,pub authority:Pubkey,pub new_authority:Pubkey,pub timestamp:i64}
#[event]
#[derive(Clone)]
pub struct ReservedFeeRecipientsEvent{pub timestamp:i64,pub reserved_fee_recipient:Pubkey,pub reserved_fee_recipients:[Pubkey;7]}








#[event]
#[derive(Clone)]
pub struct InitUserVolumeAccumulatorEvent{pub payer:Pubkey,pub user:Pubkey,pub timestamp:i64}
#[event]
#[derive(Clone)]
pub struct CloseUserVolumeAccumulatorEvent{pub user:Pubkey,pub timestamp:i64,pub total_unclaimed_tokens:u64,pub total_claimed_tokens:u64,pub current_sol_volume:u64,pub last_update_timestamp:i64}































fn update_global_authority_handler(ctx:Context<UpdateGlobalAuthority>)->Result<()>{
    ctx.accounts.global.authority=ctx.accounts.new_authority.key();
    let event=UpdateGlobalAuthorityEvent{global:ctx.accounts.global.key(),authority:ctx.accounts.authority.key(),new_authority:ctx.accounts.new_authority.key(),timestamp:Clock::get()?.unix_timestamp};
    emit!(event.clone());emit_cpi!(event);Ok(())
}

// Shared user-signed quote payment helpers.
pub mod user_quote_payments {
    use anchor_lang::prelude::*;
    use anchor_spl::token_interface::TokenInterface;
    use crate::trade_types::BondingCurve;

pub use crate::payments::uqp_transfer_native as transfer_native;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::uqp_transfer_native_unchecked as transfer_native_unchecked;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::uqp_transfer_native_curve_unchecked as transfer_native_curve_unchecked;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::user_payments::transfer_from_user as transfer_from_user;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
pub use crate::payments::uqp_transfer_native_owned as transfer_native_owned;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::user_payments::transfer_from_user_owned as transfer_from_user_owned;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
pub use crate::payments::uqp_transfer_native_curve as transfer_native_curve;
pub use crate::payments::uqp_transfer_native_recipient as transfer_native_recipient;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::user_payments::transfer_from_user_recipient as transfer_from_user_recipient;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

}

use crate::trade_types::Shareholder;













































fn create_event<'info>(name:String,symbol:String,uri:String,creator:Pubkey,mint:&Account<'info,anchor_spl::token::Mint>,user:&Signer<'info>,bonding_curve:&Account<'info,trade_types::BondingCurve>,token_program:&Program<'info,anchor_spl::token::Token>,is_mayhem_mode:bool,creator_fee_bps:u64)->Result<CreateEvent>{
 let virtual_token_reserves=bonding_curve.virtual_token_reserves;let virtual_sol_reserves=bonding_curve.virtual_quote_reserves;let real_token_reserves=bonding_curve.real_token_reserves;let token_total_supply=bonding_curve.token_total_supply;let is_holder_reward=bonding_curve.is_holder_reward;let depth=bonding_curve.depth;let quote_mint=bonding_curve.quote_mint;Ok(CreateEvent{name,symbol,uri,mint:mint.key(),bonding_curve:bonding_curve.key(),user:user.key(),creator,timestamp:Clock::get()?.unix_timestamp,virtual_token_reserves,virtual_sol_reserves,real_token_reserves,token_total_supply,token_program:token_program.key(),is_mayhem_mode,is_cashback_enabled:false,quote_mint:quote_mint,virtual_quote_reserves:virtual_sol_reserves,creator_fee_bps,is_holder_reward,depth})
}
#[inline(always)]
fn create_metadata(ctx:&Context<Create>,name:&String,symbol:&String,uri:&String,creator:Pubkey)->Result<()>{
     let a=&ctx.accounts;
     let (name,symbol,uri)=(name.clone(),symbol.clone(),uri.clone());let bump=ctx.bumps.mint_authority;let mint:&Account<anchor_spl::token::Mint>=&a.mint;let signer_seeds:&[&[&[u8]]]=&[&[b"mint-authority",&[bump]]];metadata_cpi(&(&a.mpl_token_metadata,&a.metadata,mint,&a.mint_authority,&a.user,&a.system_program,&a.rent),(name,symbol,uri),creator,signer_seeds)?;
     Ok(())
}
fn metadata_cpi<'info>(accounts:&(&Program<'info,create::MetadataProgram>,&UncheckedAccount<'info>,&Account<'info,anchor_spl::token::Mint>,&UncheckedAccount<'info>,&Signer<'info>,&Program<'info,System>,&Sysvar<'info,Rent>),metadata:(String,String,String),creator:Pubkey,signer_seeds:&[&[&[u8]]])->Result<()>{
     let (name,symbol,uri)=metadata;
     anchor_spl::metadata::create_metadata_accounts_v3(
      CpiContext::new_with_signer(accounts.0.to_account_info(),anchor_spl::metadata::CreateMetadataAccountsV3{
       metadata:accounts.1.to_account_info(),mint:accounts.2.to_account_info(),mint_authority:accounts.3.to_account_info(),payer:accounts.4.to_account_info(),update_authority:accounts.3.to_account_info(),system_program:accounts.5.to_account_info(),rent:accounts.6.to_account_info(),
      },signer_seeds),
      anchor_spl::metadata::mpl_token_metadata::types::DataV2{name,symbol,uri,seller_fee_basis_points:0,creators:Some(vec![anchor_spl::metadata::mpl_token_metadata::types::Creator{address:creator,verified:false,share:100}]),collection:None,uses:None},
      false,true,None,
     )?;
     Ok(())
}
fn mint_tokens<'info>(a:&Create<'info>,mint:&Box<Account<'info,anchor_spl::token::Mint>>,to:&Box<Account<'info,anchor_spl::token::TokenAccount>>,bump:u8)->Result<()>{
     let signer_seeds:&[&[&[u8]]]=&[&[b"mint-authority",&[bump]]];anchor_spl::token::mint_to(CpiContext::new_with_signer(a.token_program.to_account_info(),anchor_spl::token::MintTo{mint:mint.to_account_info(),to:to.to_account_info(),authority:a.mint_authority.to_account_info()},signer_seeds),a.global.token_total_supply)?;
     Ok(())
}
fn revoke_mint_authority<'info>(bump:u8,accounts:&(&Program<'info,anchor_spl::token::Token>,&Account<'info,anchor_spl::token::Mint>,&UncheckedAccount<'info>))->Result<()>{
     let signer_seeds:&[&[&[u8]]]=&[&[b"mint-authority",&[bump]]];anchor_spl::token::set_authority(CpiContext::new_with_signer(accounts.0.to_account_info(),anchor_spl::token::SetAuthority{account_or_mint:accounts.1.to_account_info(),current_authority:accounts.2.to_account_info()},signer_seeds),anchor_spl::token::spl_token::instruction::AuthorityType::MintTokens,None)?;
     Ok(())
}
