EDITS=[('let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);','let (collect_old,sharing_update,skip,hr)=if shared{if holder{(false,Some(None),false,true)}else{let r=(false,Some(args.0),true,false);'),
('None,true)};(holder,cashback,target,sharing_update,collect_old,skip)}','None,true,holder)};(hr,cashback,target,sharing_update,collect_old,skip)}'),
('curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=_holder;')]
