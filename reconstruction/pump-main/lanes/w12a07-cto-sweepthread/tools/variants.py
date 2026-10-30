# Each variant: list of (old, new) replacements on admin_cto.rs (applied in order, each must match exactly once).
V = {}
VS_OLD = "let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];"
V['vsig'] = [
 (VS_OLD, VS_OLD + "let vsigner:&[&[&[u8]];1]=&[vaultseeds];"),
 ("amount,&[vaultseeds]).map(|()|amount)", "amount,vsigner).map(|()|amount)"),
 ("amount,&[vaultseeds])?;}", "amount,vsigner)?;}"),
]
V['vsigs'] = [
 (VS_OLD, VS_OLD + "let vsigner:&[&[&[u8]]]=&[vaultseeds];"),
 ("amount,&[vaultseeds]).map(|()|amount)", "amount,vsigner).map(|()|amount)"),
 ("amount,&[vaultseeds])?;}", "amount,vsigner)?;}"),
]
V['vsiglit'] = [
 (VS_OLD, "let vsigner:&[&[&[u8]]]=&[&[b\"creator-vault\",old.as_ref(),&bump]];"),
 ("amount,&[vaultseeds]).map(|()|amount)", "amount,vsigner).map(|()|amount)"),
 ("amount,&[vaultseeds])?;}", "amount,vsigner)?;}"),
]
D_OLD = "let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}"
V['destscope'] = [
 (D_OLD, "{" + D_OLD + "}"),
]
V['vsig_dest'] = V['vsig'] + V['destscope']
V['none'] = []
W_OLD1 = "let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();"
W_NEW1 = "let coin_present=!a.coin_creator_vault_ata.data_is_empty();"
W_OLD2 = "let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;"
W_NEW2 = "let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);"
W_OLD3 = "let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;"
W_NEW3 = "let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"
V['wflags'] = [(W_OLD1,W_NEW1),(W_OLD2,W_NEW2),(W_OLD3,W_NEW3),
 ("if collection_native||(source_present&&!source_frozen){","if do_collect{"),
 ("if coin_present&&!coin_frozen{","if do_coin{")]
V['wflags_dest'] = V['wflags'] + V['destscope']
