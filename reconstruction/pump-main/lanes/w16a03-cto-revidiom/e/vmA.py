EDITS=[("sharing_update=Some(args.0);","sharing_update=Some(args.0.map(|_|target));"),
       ("validate(&st,hopt,fee,new,&holder_key,&sk)","validate(&st,hopt,fee,args.0,&holder_key,&sk)")]
