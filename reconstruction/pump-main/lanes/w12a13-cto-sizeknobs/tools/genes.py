# Base genes (from w9r2-admincto-harvest edits.py), adapted to main 20a1ae9c0 / e61df0357 admin_cto.rs.
G = {}
G['wallet_flags'] = [
    ("let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;",
     "\n  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);\n  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"),
    ("\n  if collection_native||(source_present&&!source_frozen){", "\n  if do_collect{"),
    ("\n  if coin_present&&!coin_frozen{", "\n  if do_coin{")]
G['region2_tree'] = [
    ("let sharing_update=if shared{Some(if holder{None}else{new})}else{None};let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();if shared&&!holder{target=st.creator;}",
     "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")]
G['canedit_first'] = [
    ("let old_fee=curve.creator_fee_bps;\n  curve.creator=target;", "let old_fee=curve.creator_fee_bps;curve.can_edit_creator_fee=false;\n  curve.creator=target;"),
    ("  curve.can_edit_creator_fee=false;\n (old_creator", "\n (old_creator")]
G['old_fee_first'] = [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")]
G['fee_unwrap'] = [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n")]

BASES = {
    'main': [],
    'j3': ['wallet_flags'],
    'k4': ['wallet_flags', 'region2_tree', 'fee_unwrap', 'canedit_first', 'old_fee_first'],
    # L1 = PR #2749 (w12a04-cto-k4size): k4 + s_bump_first + p_share_match (knobs.K names)
    'L1': ['wallet_flags', 'region2_tree', 'fee_unwrap', 'canedit_first', 'old_fee_first', 's_bump_first', 'p_share_match'],
}


def apply(edits, s, strict=True):
    for a, b in edits:
        c = s.count(a)
        if c != 1:
            if strict:
                raise ValueError(f'pattern count {c}: {a[:100]!r}')
            return None
        s = s.replace(a, b)
    return s


def base_text(name, main_text):
    import knobs
    s = main_text
    for g in BASES[name]:
        s = apply(G[g] if g in G else knobs.K[g], s)
    return s
