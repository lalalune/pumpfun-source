exec(open("/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a67-cto-h7src/e/common.py").read())
V="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
EDITS=[(B,B.replace('}t};','}t};Ok(target)}fn fee_check(st:&CtoState,holder:bool,fee:Option<u64>)->Result<()>{')),(C,' Ok(())}pub fn execute'),(V,'let mut target=validate(&st,hopt,fee,new,&holder_key,&sk).and_then(|t|{fee_check(&st,holder,fee)?;Ok(t)})?;')]
