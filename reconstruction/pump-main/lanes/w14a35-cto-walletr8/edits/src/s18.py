# do_coin via bool::then_some-free spelling: !coin_present||token_frozen? inverted skip flag
EDITS=[("  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","  let skip_coin=!coin_present||token_frozen(a.coin_creator_vault_ata.as_ref())?;"),("  if coin_present&do_coin{\n","  if coin_present&!skip_coin{\n")]
