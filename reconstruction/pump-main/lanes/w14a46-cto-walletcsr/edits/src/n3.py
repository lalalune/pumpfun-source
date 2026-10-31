# do_coin as frozen test only: let coin_ok=!token_frozen(..) inside coin_present; gate coin_present&coin_ok
EDITS=[("  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","  let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")]
