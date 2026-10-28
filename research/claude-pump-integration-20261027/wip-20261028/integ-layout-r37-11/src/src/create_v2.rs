use crate::*;
use spl_type_length_value::variable_len_pack::VariableLenPack;
use anchor_spl::{token_interface::{self,Mint,TokenAccount},token_2022::Token2022,associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const MAYHEM_ID:Pubkey=anchor_lang::solana_program::pubkey!("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e");const UNSUPPORTED_QUOTE_MINT:Pubkey=anchor_lang::solana_program::pubkey!("9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP");const PUMP_QUOTE_MINT:Pubkey=anchor_lang::solana_program::pubkey!("pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn");
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
pub fn execute<'info>(ctx:Context<'_,'_,'_,'info,CreateV2<'info>>,name:String,symbol:String,uri:String,creator:Pubkey,is_mayhem_mode:bool,is_cashback_enabled:OptionBool,creator_fee_bps:CreationOptionU64,is_holder_reward:OptionBool)->Result<()>{
 let a=&ctx.accounts;
 if is_mayhem_mode {
  require_eq!(a.global.mayhem_mode_enabled,true,PumpError::MayhemModeDisabled);
 }
 require!(!is_cashback_enabled.0,PumpError::CashbackDeprecated);
 let creator=if is_holder_reward.0 {require!(a.global.is_holder_reward_enabled,PumpError::HolderRewardDisabled);Pubkey::find_program_address(&[b"holder-rewards",a.mint.key().as_ref()],&crate::ID).0}else{creator};
 require_keys_neq!(creator,Pubkey::default(),PumpError::CreatorShouldNotBeZero);
 require_eq!(a.global.create_v2_enabled,true,PumpError::CreateV2Disabled);
 let mut depth=0u8;
 let (quote_mint,virtual_quote_reserves,can_configure_fee)=if ctx.remaining_accounts.is_empty(){(Pubkey::default(),a.global.initial_virtual_sol_reserves,false)}else{
  require_gte!(ctx.remaining_accounts.len(),3,PumpError::NotEnoughRemainingAccounts);
  let mint=&ctx.remaining_accounts[0];let ata=&ctx.remaining_accounts[1];let program=&ctx.remaining_accounts[2];
  require!(program.key()==anchor_spl::token::ID || program.key()==anchor_spl::token_2022::ID,PumpError::InvalidQuoteTokenProgram);
  require!(program.executable,PumpError::InvalidQuoteTokenProgram);
  if mint.key()==Pubkey::default() || mint.key()==anchor_spl::token::spl_token::native_mint::id() {
   (Pubkey::default(),a.global.initial_virtual_sol_reserves,false)
  } else {
  // Literal key rejection at 0x1f6a8, before whitelist/control selection.
  require!(mint.key()!=UNSUPPORTED_QUOTE_MINT,PumpError::UnsupportedQuoteMint);
  let (reserves,can_configure)=if a.global.whitelisted_quote_mints.contains(mint.key){(a.global.initial_virtual_quote_reserves,false)}else{
   require!(ctx.remaining_accounts.len()>=4,PumpError::UnsupportedQuoteMint);
   let control=&ctx.remaining_accounts[3];let expected=Pubkey::find_program_address(&[b"quote-control"],&crate::ID).0;
   require_keys_eq!(control.key(),expected,PumpError::InvalidQuoteControl);
   require_keys_eq!(*control.owner,crate::ID,PumpError::InvalidQuoteControl);
   let entry=nested_create::control_account(control,mint.key)?;
   if let Some(reserves)=entry {(reserves,true)} else {
    let (reserves,nested_depth)=nested_create::walk(&a.global,ctx.remaining_accounts)?;
    depth=nested_depth;
    (reserves,true)
   }
  };
  require_keys_eq!(*mint.owner,program.key(),PumpError::UnsupportedQuoteMint);
  if program.key()==anchor_spl::token_2022::ID && mint.key()!=PUMP_QUOTE_MINT {require!(quote_extensions_supported(&mint.try_borrow_data()?,true),PumpError::UnsupportedQuoteMint);}

  let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&a.bonding_curve.key(),mint.key,program.key);
  require_keys_eq!(ata.key(),expected,PumpError::InvalidAssociatedQuoteBondingCurve);
  anchor_spl::associated_token::create(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.user.to_account_info(),associated_token:ata.clone(),authority:a.bonding_curve.to_account_info(),mint:mint.clone(),system_program:a.system_program.to_account_info(),token_program:program.clone()}))?;
  (mint.key(),reserves,can_configure)
  }
 };
 if is_mayhem_mode && quote_mint!=Pubkey::default() {
  require!(a.global.whitelisted_quote_mints.contains(&quote_mint),PumpError::MayhemModeQuoteMintNotAllowed);
 }
 let fee=if can_configure_fee && creator_fee_bps.0>0 {
  require!(a.global.creator_fee_configurable,PumpError::CreatorFeeNotConfigurable);
  require!(creator_fee_bps.0<=a.global.max_configurable_creator_fee_bps,PumpError::CreatorFeeBpsOutOfRange);
  creator_fee_bps.0
 }else{0};
 require_gte!(32,name.len(),PumpError::NameTooLong);require_gte!(13,symbol.len(),PumpError::SymbolTooLong);require_gte!(200,uri.len(),PumpError::UriTooLong);
 let bump=[ctx.bumps.mint_authority];let seeds:&[&[u8]]=&[b"mint-authority",&bump];
 let metadata=anchor_spl::token_2022_extensions::spl_token_metadata_interface::state::TokenMetadata{
  name:name.clone(),symbol:symbol.clone(),uri:uri.clone(),..Default::default()
 };
 let rent_sysvar=Rent::get()?;
 let mint_info=a.mint.to_account_info();
 let base_size=mint_info.data_len().checked_add(4).ok_or_else(|| error!(PumpError::Overflow))?;
 let metadata_size=metadata.get_packed_len()?;
 let size=base_size.checked_add(metadata_size).ok_or_else(|| error!(PumpError::Overflow))?;
 let rent=rent_sysvar.minimum_balance(size).saturating_sub(mint_info.lamports());
 if rent>0 {anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to:a.mint.to_account_info()}),rent)?;}
 anchor_spl::token_2022_extensions::token_metadata_initialize(
  CpiContext::new_with_signer(a.token_program.to_account_info(),anchor_spl::token_2022_extensions::TokenMetadataInitialize{
   program_id:a.token_program.to_account_info(),metadata:a.mint.to_account_info(),update_authority:a.mint_authority.to_account_info(),mint_authority:a.mint_authority.to_account_info(),mint:a.mint.to_account_info(),
  },&[seeds]),name.clone(),symbol.clone(),uri.clone(),
 )?;
 let new_authority:anchor_spl::token_2022_extensions::spl_pod::optional_keys::OptionalNonZeroPubkey=None::<Pubkey>.try_into()?;
 anchor_spl::token_2022_extensions::token_metadata_update_authority(
  CpiContext::new_with_signer(a.token_program.to_account_info(),anchor_spl::token_2022_extensions::TokenMetadataUpdateAuthority{
   program_id:a.token_program.to_account_info(),metadata:a.mint.to_account_info(),current_authority:a.mint_authority.to_account_info(),new_authority:a.system_program.to_account_info(),
  },&[seeds]),new_authority,
 )?;
 // Mayhem-creation CPI: pump signs the ["mint-authority"] PDA into mayhem's
 // initialize_mayhem_state (disc 0x2dcc4555485ebd9d, no args). Mayhem derives the
 // mint from account #4, derives/inits mayhem_state["mayhem-state",mint] and the
 // sol-vault token vault, and sets end_timestamp=now+reset_middle[0]*3600.
 if is_mayhem_mode { initialize_mayhem(&ctx)?; }
 token_interface::mint_to(CpiContext::new_with_signer(a.token_program.to_account_info(),token_interface::MintTo{mint:a.mint.to_account_info(),to:a.associated_bonding_curve.to_account_info(),authority:a.mint_authority.to_account_info()},&[seeds]),a.global.token_total_supply)?;
 if is_mayhem_mode {
  // Mayhem mints the full supply to the sol-vault token vault as well.
  token_interface::mint_to(CpiContext::new_with_signer(a.token_program.to_account_info(),token_interface::MintTo{mint:a.mint.to_account_info(),to:a.mayhem_token_vault.to_account_info(),authority:a.mint_authority.to_account_info()},&[seeds]),a.global.token_total_supply)?;
 }
 token_interface::set_authority(CpiContext::new_with_signer(a.token_program.to_account_info(),token_interface::SetAuthority{current_authority:a.mint_authority.to_account_info(),account_or_mint:a.mint.to_account_info()},&[seeds]),token_interface::spl_token_2022::instruction::AuthorityType::MintTokens,None)?;
 let event=CreateEvent{name,symbol,uri,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),user:a.user.key(),creator,timestamp:Clock::get()?.unix_timestamp,virtual_token_reserves:a.global.initial_virtual_token_reserves,virtual_sol_reserves:virtual_quote_reserves,real_token_reserves:a.global.initial_real_token_reserves,token_total_supply:a.global.token_total_supply,token_program:a.token_program.key(),is_mayhem_mode,is_cashback_enabled:false,quote_mint,virtual_quote_reserves,creator_fee_bps:fee,is_holder_reward:is_holder_reward.0,depth};
 let g=&ctx.accounts.global;let curve=&mut ctx.accounts.bonding_curve;curve.virtual_token_reserves=g.initial_virtual_token_reserves;curve.virtual_quote_reserves=virtual_quote_reserves;curve.real_token_reserves=g.initial_real_token_reserves;curve.token_total_supply=g.token_total_supply;curve.creator=creator;curve.creator_fee_bps=fee;curve.is_holder_reward=is_holder_reward.0;curve.quote_mint=quote_mint;curve.initial_virtual_quote_reserves=virtual_quote_reserves;curve.depth=depth;curve.is_mayhem_mode=is_mayhem_mode;
 emit!(event.clone());emit_cpi!(event);Ok(())
}

// The captured program accepts transfer-fee config as well as the operable
// metadata/delegate extensions; official IDL prose omits that observed case.
#[inline(never)]
pub fn quote_extensions_supported(data:&[u8],allow_token_extensions:bool)->bool {
 if data.len()==82{return true;}
 if data.len()<167 || data[82..165].iter().any(|&b|b!=0) || data[165]!=1{return false;}
 let mut seen=0u64;
 let mut at=166usize;
 while at<data.len(){
  let remaining=data.len()-at;
  if remaining<2{return true;}
  let kind=u16::from_le_bytes([data[at],data[at+1]]);
  if kind==0{return true;}
  if remaining<4{return false;}
  let size=u16::from_le_bytes([data[at+2],data[at+3]]) as usize;
  let next=match at.checked_add(4+size){Some(next) if next<=data.len()=>next,_=>return false};
  match kind{
   18|19=>{},
   1|4|6|12|14|16|25|26=>if !allow_token_extensions{return false;},
   _=>return false,
  }
  let bit=1u64<<kind;
  if seen&bit!=0{return false;}
  let bytes=&data[at+4..next];
  match kind{
   1=>if bytes.len()<108{return false;},
   6=>if bytes.is_empty() || bytes[0]!=1{return false;},
   14=>if bytes.len()<64 || bytes[32..64]!=[0;32]{return false;},
   _=>{},
  }
  seen|=bit;
  at=next;
 }
 true
}


// Main-owned CPI caller for the observed zero-argument instruction.
#[inline(never)]
pub fn initialize_mayhem<'info>(ctx:&Context<'_, '_, '_, 'info, CreateV2<'info>>)->Result<()>{
 let a=&ctx.accounts;
 mayhem_interface::cpi::initialize_mayhem_state(CpiContext::new_with_signer(
  a.mayhem_program_id.to_account_info(),mayhem_interface::cpi::accounts::InitializeMayhemState{
   payer:a.user.to_account_info(),
   mint_authority:a.mint_authority.to_account_info(),
   sol_vault:a.sol_vault.to_account_info(),
   mint:a.mint.to_account_info(),
   token_vault:a.mayhem_token_vault.to_account_info(),
   global_params:a.global_params.to_account_info(),
   mayhem_state:a.mayhem_state.to_account_info(),
   system_program:a.system_program.to_account_info(),
   token_program:a.token_program.to_account_info(),
   associated_token_program:a.associated_token_program.to_account_info(),
  },&[&[b"mint-authority",&[ctx.bumps.mint_authority]]],
 ))
}

// Client-side instruction/account binding only; no companion implementation.
pub mod mayhem_interface {
 use super::*;
 pub mod instruction {
  use super::*;
  #[derive(AnchorSerialize,AnchorDeserialize)]
  pub struct InitializeMayhemState;
  impl Discriminator for InitializeMayhemState {const DISCRIMINATOR:&'static[u8]=&[157,189,94,72,85,69,204,45];}
  impl anchor_lang::InstructionData for InitializeMayhemState {}
 }
 pub mod cpi {
  use super::*;
  pub fn initialize_mayhem_state<'a,'b,'c,'info>(ctx:anchor_lang::context::CpiContext<'a,'b,'c,'info,accounts::InitializeMayhemState<'info>>)->anchor_lang::Result<()>{
   let ix={
    let ix=instruction::InitializeMayhemState;
    let mut data=Vec::with_capacity(256);
    data.extend_from_slice(<instruction::InitializeMayhemState as anchor_lang::Discriminator>::DISCRIMINATOR);
    AnchorSerialize::serialize(&ix,&mut data).map_err(|_|anchor_lang::error::ErrorCode::InstructionDidNotSerialize)?;
    let accounts=ctx.to_account_metas(None);
    anchor_lang::solana_program::instruction::Instruction{program_id:ctx.program.key(),accounts,data}
   };
   let mut acc_infos=ctx.to_account_infos();
   anchor_lang::solana_program::program::invoke_signed(&ix,&acc_infos,ctx.signer_seeds).map_or_else(|e|Err(Into::into(e)),|_|Ok(()))
  }
  pub mod accounts {
   use super::*;
   pub struct InitializeMayhemState<'info>{
    pub payer:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub global_params:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub mint_authority:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub sol_vault:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub mint:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub token_vault:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub mayhem_state:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub system_program:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub token_program:anchor_lang::solana_program::account_info::AccountInfo<'info>,
    pub associated_token_program:anchor_lang::solana_program::account_info::AccountInfo<'info>,
   }
   impl<'info> anchor_lang::ToAccountMetas for InitializeMayhemState<'info>{
    fn to_account_metas(&self,_is_signer:Option<bool>)->Vec<anchor_lang::solana_program::instruction::AccountMeta>{
     let mut account_metas=vec![];
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new(anchor_lang::Key::key(&self.payer),true));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.global_params),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.mint_authority),true));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new(anchor_lang::Key::key(&self.sol_vault),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.mint),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new(anchor_lang::Key::key(&self.token_vault),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new(anchor_lang::Key::key(&self.mayhem_state),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.system_program),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.token_program),false));
     account_metas.push(anchor_lang::solana_program::instruction::AccountMeta::new_readonly(anchor_lang::Key::key(&self.associated_token_program),false));
     account_metas
    }
   }
   impl<'info> anchor_lang::ToAccountInfos<'info> for InitializeMayhemState<'info>{
    fn to_account_infos(&self)->Vec<anchor_lang::solana_program::account_info::AccountInfo<'info>>{
     let mut account_infos=vec![];
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.payer));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.global_params));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.mint_authority));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.sol_vault));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.mint));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.token_vault));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.mayhem_state));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.system_program));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.token_program));
     account_infos.extend(anchor_lang::ToAccountInfos::to_account_infos(&self.associated_token_program));
     account_infos
    }
   }
  }
 }
}

mod nested_create {
//! Source hypothesis for the create-linked ancestor walk; see the publication ledger.
//! Numeric/local contracts are recovered. Framework error payloads and runtime ABI
//! remain conditional; these are natural Rust types, not an original memory layout.
use crate::{Global, PumpError};
use crate::trade_types::BondingCurve;
use anchor_lang::prelude::*;

const CURVE_DISC: [u8; 8] = [23, 183, 248, 55, 96, 216, 172, 96];
const POOL_DISC: [u8; 8] = [241, 154, 109, 4, 17, 177, 109, 188];
use crate::quote_control::state::control_entry;
const AMM: Pubkey = anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");

#[derive(Clone, Copy)]
enum Record {
    Curve { vt: u64, vq: u64, rt: u64, rq: u64, pool_base: u64, migration_fee: u64 },
    Pool { base: u64, quote: u128 },
}

fn overflow() -> anchor_lang::error::Error { error!(PumpError::Overflow) }
fn u64_at(data: &[u8], at: usize) -> u64 {
    u64::from_le_bytes(data[at..at + 8].try_into().unwrap())
}
fn key_at(data: &[u8], at: usize) -> Pubkey {
    Pubkey::new_from_array(data[at..at + 32].try_into().unwrap())
}

// The captured ancestor reader calls the shared checked historical decoder.
fn decode_curve(data: &[u8]) -> Result<BondingCurve> {
    BondingCurve::try_deserialize(&mut &data[..])
        .map_err(|_| error!(PumpError::InvalidQuoteBondingCurve))
}

fn ancestor(account: &AccountInfo<'_>, mint: &Pubkey) -> Result<BondingCurve> {
    let expected = Pubkey::find_program_address(&[b"bonding-curve", mint.as_ref()], &crate::ID).0;
    require_keys_eq!(account.key(), expected, PumpError::InvalidQuoteBondingCurve);
    require_keys_eq!(*account.owner, crate::ID, PumpError::InvalidQuoteBondingCurve);
    let data = account.try_borrow_data()?;
    decode_curve(&data)
}

#[inline(never)]
pub(super) fn control_account(account: &AccountInfo<'_>, mint: &Pubkey) -> Result<Option<u64>> {
    let data = account.try_borrow_data()?;
    control_entry(&data, mint)
}

fn root_seed(g: &Global, quote: &Pubkey, control: &[u8]) -> Result<u64> {
    if quote == &Pubkey::default() { return Ok(g.initial_virtual_sol_reserves); }
    if quote == &anchor_spl::token::spl_token::native_mint::id()
        || g.whitelisted_quote_mints.contains(quote) {
        return Ok(g.initial_virtual_quote_reserves);
    }
    control_entry(control, quote)?.ok_or_else(|| error!(PumpError::QuoteBondingCurveNotEligible))
}

fn vault_amount(account: &AccountInfo<'_>, data: &[u8]) -> Result<u64> {
    require!(account.owner == &anchor_spl::token::ID || account.owner == &anchor_spl::token_2022::ID,
        PumpError::InvalidQuotePool);
    require_gte!(data.len(), 165usize, PumpError::InvalidQuotePool);
    require_neq!(data.len(), 355usize, PumpError::InvalidQuotePool);
    require_eq!(data[108], 1u8, PumpError::InvalidQuotePool);
    if data.len() != 165 { require_eq!(data[165], 2u8, PumpError::InvalidQuotePool); }
    Ok(u64_at(data, 64))
}

fn pool_record(mint: &Pubkey, quote: &Pubkey, pool: &AccountInfo<'_>,
    base: &AccountInfo<'_>, quote_vault: &AccountInfo<'_>) -> Result<Record> {
    let authority = Pubkey::find_program_address(&[b"pool-authority", mint.as_ref()], &crate::ID).0;
    let pool_quote = if quote == &Pubkey::default() {
        anchor_spl::token::spl_token::native_mint::id()
    } else { *quote };
    let expected = Pubkey::find_program_address(
        &[b"pool", &0u16.to_le_bytes(), authority.as_ref(), mint.as_ref(), pool_quote.as_ref()], &AMM).0;
    // All three borrows precede key/owner validation; retain their lifetimes.
    let pool_data = pool.try_borrow_data()?;
    let base_data = base.try_borrow_data()?;
    let quote_data = quote_vault.try_borrow_data()?;
    require_keys_eq!(pool.key(), expected, PumpError::InvalidQuotePool);
    require_keys_eq!(*pool.owner, AMM, PumpError::QuotePoolNotFound);
    require!(pool_data.len() >= 211, PumpError::InvalidQuotePool);
    require!(pool_data[..8] == POOL_DISC, PumpError::InvalidQuotePool);
    let base_key = key_at(&pool_data, 139);
    let quote_key = key_at(&pool_data, 171);
    let adjustment = if pool_data.len() >= 261 {
        i128::from_le_bytes(pool_data[245..261].try_into().unwrap())
    } else { 0 };
    require_keys_eq!(base.key(), base_key, PumpError::InvalidQuotePool);
    require_keys_eq!(quote_vault.key(), quote_key, PumpError::InvalidQuotePool);
    let base_amount = vault_amount(base, &base_data)?;
    let quote_amount = vault_amount(quote_vault, &quote_data)?;
    let adjusted = (quote_amount as i128).checked_add(adjustment).ok_or_else(overflow)?;
    require!(adjusted >= 0, PumpError::Overflow);
    Ok(Record::Pool { base: base_amount, quote: adjusted as u128 })
}

pub(super) fn walk(g: &Global, accounts: &[AccountInfo<'_>]) -> Result<(u64, u8)> {
    // Slicing preserves the original <4 bounds failure. The ordinary caller has
    // already admitted the prefix; exactly four is UnsupportedQuoteMint.
    let mut tail = &accounts[4..];
    let first = tail.first().ok_or_else(|| error!(PumpError::UnsupportedQuoteMint))?;
    let mut mint = *accounts[0].key;
    let mut curve = ancestor(first, &mint)?;
    let depth = curve.depth.checked_add(1).ok_or_else(overflow)?;
    require_gte!(g.max_curve_depth.min(5), depth, PumpError::CurveDepthExceeded);
    require!(!curve.is_mayhem_mode, PumpError::QuoteBondingCurveNotEligible);
    // Five logical slots; inactive storage has no Pool tail interpretation.
    let mut records = [Record::Pool { base: 0, quote: 0 }; 5];
    let mut seed = 0;
    for position in 0..usize::from(depth) {
        if position != 0 {
            mint = curve.quote_mint;
// layout-pad(30): aligns the next Source site with the original line





























            let account = tail.first().ok_or_else(|| error!(PumpError::QuoteChainAccountsRequired))?;
            curve = ancestor(account, &mint)?;
        }
        if position + 1 == usize::from(depth) {
            let control = accounts[3].try_borrow_data()?;
            seed = root_seed(g, &curve.quote_mint, &control)?;
        }
        if curve.virtual_token_reserves == 0 && curve.virtual_quote_reserves == 0
            && curve.real_token_reserves == 0 && curve.real_quote_reserves == 0 {
            require!(tail.len() >= 4, PumpError::QuotePoolAccountsRequired);
            records[position] = pool_record(&mint, &curve.quote_mint, &tail[1], &tail[2], &tail[3])?;
            tail = &tail[4..];
        } else {
            require!(!curve.complete, PumpError::QuoteCurveAwaitingMigration);
            let pool_base = curve.token_total_supply.checked_sub(g.initial_real_token_reserves).ok_or_else(overflow)?;
            records[position] = Record::Curve {
                vt: curve.virtual_token_reserves, vq: curve.virtual_quote_reserves,
                rt: curve.real_token_reserves, rq: curve.real_quote_reserves, pool_base,
                migration_fee: if curve.quote_mint == Pubkey::default() { g.pool_migration_fee } else { 0 },
            };
            tail = &tail[1..];
        }
    }
    // No positional-depth equality, repeated eligibility, or tail-count guard.
    Ok((price(g, seed, &records[..usize::from(depth)])?, depth))
}

fn constant_product(base: u64, quote: u128, amount: u128) -> Result<u128> {
    require!(quote != 0, PumpError::DivisionByZero);
    let denominator = quote.checked_add(amount).ok_or_else(overflow)?;
    let numerator = (base as u128).checked_mul(amount).ok_or_else(overflow)?;
    require!(denominator != 0, PumpError::DivisionByZero);
    Ok(numerator / denominator)
}

fn convert(record: Record, amount: u128) -> Result<u128> {
    match record {
        Record::Pool { base, quote } => constant_product(base, quote, amount),
        Record::Curve { vt, vq, rt, rq, pool_base, migration_fee } => {
            let output = constant_product(vt, vq as u128, amount)?;
            if output <= rt as u128 { return Ok(output); }
            let numerator = rt as u128 * vq as u128;
            let denominator = vt.checked_sub(rt).ok_or_else(overflow)?;
            require!(denominator != 0, PumpError::DivisionByZero);
            // Bounded u64 operands guarantee that this floor-plus-one fits u128.
            let completion = numerator / denominator as u128 + 1;
            let remainder = amount.saturating_sub(completion);
            if remainder <= 1 { return Ok(rt as u128); }
            let pool_quote = (completion + rq as u128)
                .checked_sub(migration_fee as u128).ok_or_else(overflow)?;
            let extra = constant_product(pool_base, pool_quote, remainder - 1)?;
            (rt as u128).checked_add(extra).ok_or_else(overflow)
        }
    }
}

fn price(g: &Global, seed: u64, records: &[Record]) -> Result<u64> {
    let real = g.initial_real_token_reserves;
    let numerator = real as u128 * seed as u128;
    let difference = g.initial_virtual_token_reserves.checked_sub(real).ok_or_else(overflow)?;
    require!(difference != 0, PumpError::DivisionByZero);
    let mut amount = numerator / difference as u128;
    for record in records.iter().rev() { amount = convert(*record, amount)?; }
    let difference = g.initial_virtual_token_reserves.checked_sub(real).ok_or_else(overflow)?;
    let numerator = amount.checked_mul(difference as u128).ok_or_else(overflow)?;
    require!(real != 0, PumpError::DivisionByZero);
    let reserves = u64::try_from(numerator / real as u128).map_err(|_| overflow())?;
    require_gte!(reserves, 1, PumpError::QuoteReservesOutOfRange);
    Ok(reserves)
}
}
