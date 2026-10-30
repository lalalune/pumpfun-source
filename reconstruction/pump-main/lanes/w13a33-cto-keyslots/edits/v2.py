EDITS=[
("let args=&(new,);","let args=&(new,holder_key);"),
("validate(&st,hopt,fee,new,&holder_key,&sk)?","validate(&st,hopt,fee,new,&args.1,&sk)?"),
]
