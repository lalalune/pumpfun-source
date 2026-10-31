EDITS=[('let sk=a.sharing_config.key();let mut target=validate(', 'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate('), ('(!st.holder_reward&&st.creator!=Pubkey::default(),true)', '(!st.holder_reward&&creator!=Pubkey::default(),true)')]
HYP='creator local before validate used only by the non-shared memcmp'
