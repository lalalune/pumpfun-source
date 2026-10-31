EDITS=[('let sk=a.sharing_config.key();let mut target=validate(', 'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate('), ('sharing_update=Some(args.0);target=a.bonding_curve.creator;', 'sharing_update=Some(args.0);target=creator;'), ('if collect_old{wallet(&ctx)?;}', 'collect_old.then(||wallet(&ctx)).transpose()?;')]
HYP='g1 + c2 (wallet gate then().transpose)'
