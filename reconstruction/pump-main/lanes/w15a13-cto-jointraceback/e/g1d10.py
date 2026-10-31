EDITS=[('let sk=a.sharing_config.key();let mut target=validate(', 'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate('), ('sharing_update=Some(args.0);target=a.bonding_curve.creator;', 'sharing_update=Some(args.0);target=creator;'), ('let hopt=holder;let holder=hopt==Some(true);', 'let hopt=holder;let holder=matches!(hopt,Some(true));')]
HYP='g1 + d10 (matches! holder)'
