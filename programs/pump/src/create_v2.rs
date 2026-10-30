use crate::*;
use spl_type_length_value::variable_len_pack::VariableLenPack;
use anchor_spl::{token_interface::{self,Mint,TokenAccount},token_2022::Token2022,associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub use crate::mayhem::ID as MAYHEM_ID;const UNSUPPORTED_QUOTE_MINT:Pubkey=anchor_lang::solana_program::pubkey!("9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP");const PUMP_QUOTE_MINT:Pubkey=anchor_lang::solana_program::pubkey!("pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn");
#[derive(AnchorSerialize,Clone)]
pub struct CreationOptionU64(pub u64);
impl AnchorDeserialize for CreationOptionU64 {
 fn deserialize_reader<R:std::io::Read>(reader:&mut R)->std::io::Result<Self>{let mut bytes=[0;8];match reader.read_exact(&mut bytes){Ok(())=>Ok(Self(u64::from_le_bytes(bytes))),Err(e) if e.kind()==std::io::ErrorKind::UnexpectedEof=>Ok(Self(0)),Err(e)=>Err(e)}}
}
// layout-pad(15): aligns the next Source site with the original line














#[event_cpi]
#[derive(Accounts)]
pub struct CreateV2<'info>{
 #[account(init,payer=user,mint::decimals=6,mint::authority=mint_authority,mint::token_program=token_program,extensions::metadata_pointer::metadata_address=mint)]
 pub mint:InterfaceAccount<'info,Mint>,
 /// CHECK: canonical mint authority.
 #[account(seeds=[b"mint-authority"],bump)]pub mint_authority:UncheckedAccount<'info>,
 #[account(init,payer=user,space=166,seeds=[b"bonding-curve",mint.key().as_ref()],bump)]pub bonding_curve:Box<Account<'info,trade_types::BondingCurve>>,
 #[account(init,payer=user,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub token_program:Program<'info,Token2022>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 /// CHECK: fixed CPI program; Mayhem invocation outside this bounded branch.
 #[account(mut,address=MAYHEM_ID)]pub mayhem_program_id:UncheckedAccount<'info>,
 /// CHECK: canonical Mayhem account, unused for normal creation.
 #[account(seeds=[b"global-params"],bump,seeds::program=MAYHEM_ID)]pub global_params:UncheckedAccount<'info>,
 /// CHECK: canonical Mayhem account, unused for normal creation.
 #[account(mut,seeds=[b"sol-vault"],bump,seeds::program=MAYHEM_ID)]pub sol_vault:UncheckedAccount<'info>,
 /// CHECK: canonical Mayhem account, unused for normal creation.
 #[account(mut,seeds=[b"mayhem-state",mint.key().as_ref()],bump,seeds::program=MAYHEM_ID)]pub mayhem_state:UncheckedAccount<'info>,
 /// CHECK: unused for normal creation.
 #[account(mut)]pub mayhem_token_vault:UncheckedAccount<'info>,
}
pub use crate::payments::initialize_mayhem;
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

// Client-side instruction/account binding only; no companion implementation.
pub use crate::mayhem as mayhem_interface;








































































pub use pump_token_ext::quote_extensions_supported;
pub const MAX_NAME_LENGTH:usize=32;pub const MAX_SYMBOL_LENGTH:usize=13;pub const MAX_URI_LENGTH:usize=200;
pub enum QuoteSource { Sol, Whitelisted, Controlled, Nested(u8) }


















































fn validate_quote_mint<'info>(ctx:&Context<'_,'_,'_,'info,CreateV2<'info>>,remaining_accounts:&[AccountInfo<'info>])->Result<(Pubkey,Option<u64>,QuoteSource)>{
 if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}
 require_gte!(remaining_accounts.len(),3,PumpError::NotEnoughRemainingAccounts);
 let a=&ctx.accounts;
 let mint=&remaining_accounts[0];
 let ata=&remaining_accounts[1];
 let program=&remaining_accounts[2];
 let program_key=program.key();

 require!(program_key==anchor_spl::token::ID || program_key==anchor_spl::token_2022::ID,PumpError::InvalidQuoteTokenProgram);




 require!(program.executable,PumpError::InvalidQuoteTokenProgram);
 let mint_key=mint.key();
 if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key==Pubkey::default() {
  return Ok((Pubkey::default(),None,QuoteSource::Sol));
 }





 require_keys_neq!(mint_key,UNSUPPORTED_QUOTE_MINT,PumpError::UnsupportedQuoteMint);
 let (source,reserves)=if crate::pump_quote::global_quote(mint.key(),&a.global) {
  (QuoteSource::Whitelisted,None)
 } else {
  let control=nested_create::quote_control(remaining_accounts.get(3))?;
  match nested_create::control_account(control,mint_key)? {
   Some(reserves)=>(QuoteSource::Controlled,Some(reserves)),
   None=>{
    let (reserves,depth)=nested_create::walk(remaining_accounts,&a.global)?;
    (QuoteSource::Nested(depth),Some(reserves))
   }
  }
 };










 require_keys_eq!(*mint.owner,program_key,PumpError::UnsupportedQuoteMint);
 if *mint.owner==anchor_spl::token_2022::ID && mint_key!=PUMP_QUOTE_MINT {
  check_quote_mint_extensions(mint)?;
 }
 let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&a.bonding_curve.key(),&mint_key,&program_key);










 require_keys_eq!(ata.key(),expected,PumpError::InvalidAssociatedQuoteBondingCurve);
 let ix=anchor_spl::associated_token::spl_associated_token_account::instruction::create_associated_token_account(&a.user.key(),&a.bonding_curve.key(),&mint_key,&program_key);
 anchor_lang::solana_program::program::invoke(&ix,&[a.user.to_account_info(),ata.clone(),a.bonding_curve.to_account_info(),mint.clone(),a.system_program.to_account_info(),program.clone()])?;

 Ok((mint_key,reserves,source))
}






pub(crate) mod nested_create {
//! Source hypothesis for the create-linked ancestor walk; see the publication ledger.
//! Numeric/local contracts are recovered. Framework error payloads and runtime ABI
//! remain conditional; these are natural Rust types, not an original memory layout.
use crate::{Global, PumpError};
use crate::trade_types::BondingCurve;
use anchor_lang::prelude::*;

const CURVE_DISC: [u8; 8] = [23, 183, 248, 55, 96, 216, 172, 96];
use crate::quote_control::state::control_entry;use crate::pump_quote::price;



use crate::pump_quote::{Record, depth, pool_record, AMM}; const EMPTY_RECORD: Record = Record::Pool { base: 0, quote: 0 };





pub(crate) fn overflow() -> anchor_lang::error::Error { error!(PumpError::Overflow) }







// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

// layout-pad(39): aligns the next Source site with the original line






































// Quote-control account admission (remaining_accounts[3]).
#[inline(never)]
pub(super) fn quote_control<'a, 'info>(account: Option<&'a AccountInfo<'info>>) -> Result<&'a AccountInfo<'info>> {
    let control = account.ok_or_else(|| error!(PumpError::UnsupportedQuoteMint))?;
    let expected = Pubkey::find_program_address(&[b"quote-control"], &crate::ID).0;

    require_keys_eq!(control.key(), expected, PumpError::InvalidQuoteControl);
// layout-pad(4)



    require_keys_eq!(*control.owner, crate::ID, PumpError::InvalidQuoteControl);
    Ok(control)
}
// layout-pad(28)



#[inline(never)]
pub(super) fn control_account(account: &AccountInfo<'_>, mint: Pubkey) -> Result<Option<u64>> {
    let data = account.try_borrow_data()?;
    control_entry(&data, &mint)
}



















pub(super) fn walk(accounts: &[AccountInfo<'_>], g: &Global) -> Result<(u64, u8)> {
    let quote_control_ai = &accounts[3];
    let mut mint = *accounts[0].key;
    let mut tail = &accounts[4..];


    let mut curve = ancestor({ require!(!tail.is_empty(), PumpError::UnsupportedQuoteMint); &tail[0] }, &mint)?;
// layout-pad(3)


    let depth = depth(&curve, g)?;
    require!(!curve.is_mayhem_mode, PumpError::QuoteBondingCurveNotEligible);
// layout-pad(10)









    let root = usize::from(curve.depth);
    let mut records = [EMPTY_RECORD; 5];
    let mut seed = 0;
    for (position, slot) in records.iter_mut().enumerate().take(usize::from(depth)) {
        if position != 0 {
            mint = curve.quote_mint;
            let account = tail.first().ok_or_else(|| error!(PumpError::QuoteChainAccountsRequired))?;
            curve = ancestor(account, &mint)?;
        }
        if position == root {
            let control = quote_control_ai.try_borrow_data()?;
            seed = crate::pump_quote::root_seed(&curve, g, &control)?;
        }
        *slot = record(&curve, g, &mint, &mut tail)?;
    }
// layout-pad(5)




    let num_hops = usize::from(depth); Ok((price(seed, &records[..num_hops], g)?, depth))
}
// layout-pad(7)






fn ancestor(account: &AccountInfo<'_>, mint: &Pubkey) -> Result<BondingCurve> {
    let expected = Pubkey::find_program_address(&[b"bonding-curve", mint.as_ref()], &crate::ID).0;
    require_keys_eq!(account.key(), expected, PumpError::InvalidQuoteBondingCurve);
// layout-pad(4)



    require_keys_eq!(*account.owner, crate::ID, PumpError::InvalidQuoteBondingCurve);
    let data = account.try_borrow_data()?;
// layout-pad(5)




    BondingCurve::try_deserialize(&mut &data[..]).map_err(|_| error!(PumpError::InvalidQuoteBondingCurve))
}
// layout-pad(12)











fn record(curve: &BondingCurve, g: &Global, mint: &Pubkey, tail: &mut &[AccountInfo<'_>]) -> Result<Record> {
    if curve.real_quote_reserves != 0 || curve.virtual_quote_reserves != 0
            || curve.real_token_reserves != 0 || curve.virtual_token_reserves != 0 {
        require!(!curve.complete, PumpError::QuoteCurveAwaitingMigration);
// layout-pad(6)





        let pool_base = curve.token_total_supply.checked_sub(g.initial_real_token_reserves).ok_or_else(|| error!(PumpError::Overflow))?; let migration_fee = if curve.quote_mint == Pubkey::default() { g.pool_migration_fee } else { 0 };
// layout-pad(14)













     *tail = &tail[1..];
// layout-pad(2)

        Ok(Record::Curve { vt: curve.virtual_token_reserves, vq: curve.virtual_quote_reserves, rt: curve.real_token_reserves, rq: curve.real_quote_reserves, pool_base, migration_fee })
    } else {
        let [_, pool, base_vault, quote_vault, rest @ ..] = *tail else { return Err(error!(PumpError::QuotePoolAccountsRequired)) };
        let authority = Pubkey::find_program_address(&[b"pool-authority", mint.as_ref()], &crate::ID).0; let pool_quote = if curve.quote_mint == Pubkey::default() { anchor_spl::token::spl_token::native_mint::id() } else { curve.quote_mint }; let expected = Pubkey::find_program_address(&[b"pool", &0u16.to_le_bytes(), authority.as_ref(), mint.as_ref(), pool_quote.as_ref()], &AMM).0;
        let (base, quote) = pool_record(pool, &expected, base_vault, quote_vault)?;
        *tail = rest;
        Ok(Record::Pool { base, quote })
    }
}
// layout-pad(8)







}
// layout-pad(16)















#[inline(never)]
fn check_quote_mint_extensions(mint:&AccountInfo)->Result<()>{
 let data=mint.try_borrow_data()?;
 require!(quote_extensions_supported(&data,true),PumpError::UnsupportedQuoteMint);
 Ok(())
}

// layout-pad
// layout-pad
// layout-pad
// layout-pad




fn validate_metadata(name:&str,symbol:&str,uri:&str)->Result<()>{
 require_gte!(MAX_NAME_LENGTH,name.len(),PumpError::NameTooLong);





 require_gte!(MAX_SYMBOL_LENGTH,symbol.len(),PumpError::SymbolTooLong);





 require_gte!(MAX_URI_LENGTH,uri.len(),PumpError::UriTooLong);
 Ok(())
}

























#[inline(never)]
fn initialize_metadata<'info>(ctx:&Context<'_,'_,'_,'info,CreateV2<'info>>,name:String,symbol:String,uri:String)->Result<()>{let a=&ctx.accounts;let bump=ctx.bumps.mint_authority;
 let metadata=anchor_spl::token_2022_extensions::spl_token_metadata_interface::state::TokenMetadata{name:name.clone(),symbol:symbol.clone(),uri:uri.clone(),update_authority:anchor_spl::token_2022_extensions::spl_pod::optional_keys::OptionalNonZeroPubkey(a.mint_authority.key()),mint:a.mint.key(),additional_metadata:vec![]};
 let minimum=Rent::get()?
  .minimum_balance(
  a.mint.to_account_info().data_len().checked_add(4).ok_or_else(|| error!(PumpError::Overflow))?
   .checked_add(metadata.get_packed_len()?)
   .ok_or_else(|| error!(PumpError::Overflow))?);
 let rent=minimum.checked_sub(a.mint.to_account_info().lamports()).unwrap_or(0);
 transfer_rent(a,rent)?;
 metadata_cpi(&(&a.token_program,&a.mint,&a.mint_authority),(name,symbol,uri),&[&[b"mint-authority",&[bump]]])?;
 update_metadata_authority(bump,&(&a.token_program,&a.mint,&a.mint_authority))
}
fn transfer_rent<'info>(a:&CreateV2<'info>,rent:u64)->Result<()>{
 if rent>0 {anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to:a.mint.to_account_info()}),rent)?;}
 Ok(())
}
fn metadata_cpi<'info>(accounts:&(&Program<'info,Token2022>,&InterfaceAccount<'info,Mint>,&UncheckedAccount<'info>),metadata:(String,String,String),signer_seeds:&[&[&[u8]]])->Result<()>{ anchor_spl::token_2022_extensions::token_metadata_initialize(CpiContext::new_with_signer(accounts.0.to_account_info(),anchor_spl::token_2022_extensions::TokenMetadataInitialize{mint:accounts.1.to_account_info(),metadata:accounts.1.to_account_info(),program_id:accounts.0.to_account_info(),update_authority:accounts.2.to_account_info(),mint_authority:accounts.2.to_account_info()},signer_seeds),metadata.0,metadata.1,metadata.2)?; Ok(()) }

#[inline(never)]
fn mint_supply<'info>(ctx:&Context<'_,'_,'_,'info,CreateV2<'info>>,is_mayhem_mode:bool)->Result<()>{
 let a=&ctx.accounts;let bump=ctx.bumps.mint_authority;
 mint_tokens(a,&*a.associated_bonding_curve,&a.global,&[&[b"mint-authority",&[bump]]])?;
 if is_mayhem_mode {
  mint_tokens(a,&a.mayhem_token_vault,&a.global,&[&[b"mint-authority",&[bump]]])?;
 }
 let signer:&[&[&[u8]]]=&[&[b"mint-authority",&[bump]]];
 token_interface::set_authority(CpiContext::new_with_signer(a.token_program.to_account_info(),token_interface::SetAuthority{account_or_mint:a.mint.to_account_info(),current_authority:a.mint_authority.to_account_info()},signer),token_interface::spl_token_2022::instruction::AuthorityType::MintTokens,None)
}

#[inline(never)]
fn update_metadata_authority<'info>(bump:u8,accounts:&(&Program<'info,Token2022>,&InterfaceAccount<'info,Mint>,&UncheckedAccount<'info>))->Result<()>{
 revoke_update_authority(accounts,&[&[b"mint-authority",&[bump]]])
}
#[inline(always)]
fn revoke_update_authority<'info>(accounts:&(&Program<'info,Token2022>,&InterfaceAccount<'info,Mint>,&UncheckedAccount<'info>),signer:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022_extensions::token_metadata_update_authority(CpiContext::new_with_signer(accounts.0.to_account_info(),anchor_spl::token_2022_extensions::TokenMetadataUpdateAuthority{program_id:accounts.0.to_account_info(),metadata:accounts.1.to_account_info(),current_authority:accounts.2.to_account_info(),new_authority:accounts.1.to_account_info()},signer),anchor_spl::token_2022_extensions::spl_pod::optional_keys::OptionalNonZeroPubkey::try_from(None)?)
}
#[inline(always)]
fn mint_tokens<'info,T:ToAccountInfo<'info>>(a:&CreateV2<'info>,to:&T,global:&Account<'info,Global>,signer:&[&[&[u8]]])->Result<()>{
 token_interface::mint_to(CpiContext::new_with_signer(a.token_program.to_account_info(),token_interface::MintTo{mint:a.mint.to_account_info(),to:to.to_account_info(),authority:a.mint_authority.to_account_info()},signer),global.token_total_supply)
}



















































































pub fn execute<'info>(ctx:Context<'_,'_,'_,'info,CreateV2<'info>>,name:String,symbol:String,uri:String,creator:Pubkey,is_mayhem_mode:bool,is_cashback_enabled:OptionBool,creator_fee_bps:CreationOptionU64,is_holder_reward:OptionBool)->Result<()>{
 let a=&ctx.accounts;
 if is_mayhem_mode {
  require_eq!(a.global.mayhem_mode_enabled,true,PumpError::MayhemModeDisabled);
 }





 require!(!is_cashback_enabled.0,PumpError::CashbackDeprecated);

 let creator=if is_holder_reward.0 {
  require!(a.global.is_holder_reward_enabled,PumpError::HolderRewardDisabled);
  Pubkey::find_program_address(&[b"holder-rewards",a.mint.key().as_ref()],&crate::ID).0
 } else {
  creator
 };








 require_keys_neq!(creator,Pubkey::default(),PumpError::CreatorShouldNotBeZero);





 require_eq!(a.global.create_v2_enabled,true,PumpError::CreateV2Disabled);
 let (quote_mint,reserves,source)=validate_quote_mint(&ctx,ctx.remaining_accounts)?;
















 if is_mayhem_mode {

  require!(crate::pump_quote::global_quote(quote_mint,&a.global),PumpError::MayhemModeQuoteMintNotAllowed);
 }












 let mut fee=0;if matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) && creator_fee_bps.0>0 {

  require!(a.global.creator_fee_configurable,PumpError::CreatorFeeNotConfigurable);



  require!(creator_fee_bps.0<=a.global.max_configurable_creator_fee_bps,PumpError::CreatorFeeBpsOutOfRange);
  fee=creator_fee_bps.0;
 }



 let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};
 ctx.accounts.init_curve(creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);


















 validate_metadata(&name,&symbol,&uri)?;
 let a=&ctx.accounts;
 initialize_metadata(&ctx,name.clone(),symbol.clone(),uri.clone())?;
 if is_mayhem_mode { initialize_mayhem(&ctx)?; }
 mint_supply(&ctx,is_mayhem_mode)?;
 let event=create_event(name,symbol,uri,creator,&a.mint,&a.user,&a.bonding_curve,&a.token_program,is_mayhem_mode,fee)?;
 emit!(event);emit_cpi!(event);Ok(())
}
#[inline(never)]
fn create_event<'info>(name:String,symbol:String,uri:String,creator:Pubkey,mint:&InterfaceAccount<'info,Mint>,user:&Signer<'info>,bonding_curve:&Account<'info,trade_types::BondingCurve>,token_program:&Program<'info,Token2022>,is_mayhem_mode:bool,creator_fee_bps:u64)->Result<CreateEvent>{
 let virtual_token_reserves=bonding_curve.virtual_token_reserves;let virtual_sol_reserves=bonding_curve.virtual_quote_reserves;let real_token_reserves=bonding_curve.real_token_reserves;let token_total_supply=bonding_curve.token_total_supply;let is_holder_reward=bonding_curve.is_holder_reward;let depth=bonding_curve.depth;let quote_mint=bonding_curve.quote_mint;Ok(CreateEvent{name,symbol,uri,mint:mint.key(),bonding_curve:bonding_curve.key(),user:user.key(),creator,timestamp:Clock::get()?.unix_timestamp,virtual_token_reserves,virtual_sol_reserves,real_token_reserves,token_total_supply,token_program:token_program.key(),is_mayhem_mode,is_cashback_enabled:false,quote_mint:quote_mint,virtual_quote_reserves:virtual_sol_reserves,creator_fee_bps,is_holder_reward,depth})
}
impl<'info> CreateV2<'info> {
fn init_curve(&mut self,creator:Pubkey,quote_mint:Pubkey,reserves:Option<u64>,depth:u8,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){
 let global:&Global=&self.global;
 let bonding_curve:&mut trade_types::BondingCurve=&mut self.bonding_curve;
 let sol=Pubkey::default();
 let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;
 let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};
 bonding_curve.creator=creator;
 bonding_curve.initial_virtual_quote_reserves=virtual_quote_reserves;
 bonding_curve.virtual_token_reserves=global.initial_virtual_token_reserves;
 bonding_curve.virtual_quote_reserves=virtual_quote_reserves;
 bonding_curve.real_token_reserves=global.initial_real_token_reserves;
 bonding_curve.real_quote_reserves=0;
 bonding_curve.token_total_supply=global.token_total_supply;
 bonding_curve.is_mayhem_mode=is_mayhem_mode;
 bonding_curve.is_cashback_coin=false;
 bonding_curve.quote_mint=quote_mint;
 bonding_curve.creator_fee_bps=fee;
 bonding_curve.can_edit_creator_fee=false;
 bonding_curve.is_holder_reward=is_holder_reward;
 bonding_curve.depth=depth;
 bonding_curve.post_complete_base_out=0;
 bonding_curve.post_complete_quote_in=0;
}
}
