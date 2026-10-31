EDITS=[('let sk=a.sharing_config.key();let mut target=validate(', 'let sk=a.sharing_config.key();let creator=Pubkey::new_from_array(st.creator.to_bytes());let mut target=validate('), ('sharing_update=Some(args.0);target=a.bonding_curve.creator;', 'sharing_update=Some(args.0);target=creator;')]
HYP='g1 with Pubkey::new_from_array(st.creator.to_bytes())'
