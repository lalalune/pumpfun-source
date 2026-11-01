use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    program::invoke,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

fn process_instruction(_program_id: &Pubkey, accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let token = next_account_info(iter)?;
    let input_mint = next_account_info(iter)?;
    let input_from = next_account_info(iter)?;
    let input_to = next_account_info(iter)?;
    let output_mint = next_account_info(iter)?;
    let output_to = next_account_info(iter)?;
    let authority = next_account_info(iter)?;
    let input = u64::from_le_bytes(data[0..8].try_into().unwrap());
    let output = u64::from_le_bytes(data[8..16].try_into().unwrap());
    let decimals = data[16];
    let mut transfer_data = vec![12];
    transfer_data.extend_from_slice(&input.to_le_bytes());
    transfer_data.push(decimals);
    invoke(&Instruction {
        program_id: *token.key,
        accounts: vec![
            AccountMeta::new(*input_from.key, false),
            AccountMeta::new(*input_mint.key, false),
            AccountMeta::new(*input_to.key, false),
            AccountMeta::new_readonly(*authority.key, true),
        ],
        data: transfer_data,
    }, &[input_from.clone(), input_mint.clone(), input_to.clone(), authority.clone(), token.clone()])?;
    let mut mint_data = vec![14];
    mint_data.extend_from_slice(&output.to_le_bytes());
    mint_data.push(decimals);
    invoke(&Instruction {
        program_id: *token.key,
        accounts: vec![
            AccountMeta::new(*output_mint.key, false),
            AccountMeta::new(*output_to.key, false),
            AccountMeta::new_readonly(*authority.key, true),
        ],
        data: mint_data,
    }, &[output_mint.clone(), output_to.clone(), authority.clone(), token.clone()])
}
