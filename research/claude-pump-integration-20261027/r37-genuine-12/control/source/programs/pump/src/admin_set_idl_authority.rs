use crate::*;
#[event_cpi]
#[derive(Accounts)]
pub struct AdminSetIdlAuthority<'info> {
    pub authority: Signer<'info>,
    #[account(seeds=[b"global"],bump,has_one=authority @ PumpError::NotAuthorized)]
    pub global: Account<'info,Global>,
    /// CHECK: canonical Anchor IDL account, checked and resized by the handler.
    #[account(mut,address=anchor_lang::idl::IdlAccount::address(&crate::ID))]
    pub idl_account: AccountInfo<'info>,
    pub system_program: Program<'info,System>,
    /// CHECK: the program signs its own canonical empty-seed PDA.
    #[account(seeds=[],bump)]
    pub program_signer: AccountInfo<'info>,
}
pub fn execute(ctx:Context<AdminSetIdlAuthority>,idl_authority:Pubkey)->Result<()> {
    let account=&ctx.accounts.idl_account;
    if account.owner==&ctx.accounts.system_program.key() {
        let accounts=anchor_lang::system_program::TransferWithSeed {
            from:account.clone(),
            base:ctx.accounts.program_signer.to_account_info(),
            to:ctx.accounts.authority.to_account_info(),
        };
        anchor_lang::system_program::transfer_with_seed(
            CpiContext::new_with_signer(
                ctx.accounts.system_program.to_account_info(),
                accounts,
                &[&[&[ctx.bumps.program_signer]]],
            ),
            String::from("anchor:idl"),
            &crate::ID,
            account.lamports(),
        )?;
        return Ok(());
    } else {
        require!(account.owner==&crate::ID,PumpError::AccountTypeNotSupported);
        account.realloc(10240,false)?;
        require!(account.data_len()>=8,PumpError::AccountTypeNotSupported);
        require!(account.try_borrow_data()?[..8]==[24,70,98,191,58,144,123,158],PumpError::AccountTypeNotSupported);
    }
    let mut header=anchor_lang::idl::IdlAccount::try_deserialize(&mut &account.data.borrow()[..])?;
    header.authority=idl_authority;
    header.try_serialize(&mut &mut account.data.borrow_mut()[..])?;
    let event=AdminSetIdlAuthorityEvent{idl_authority};emit!(event.clone());emit_cpi!(event);Ok(())
}
#[event]
#[derive(Clone)]
pub struct AdminSetIdlAuthorityEvent {pub idl_authority:Pubkey}
