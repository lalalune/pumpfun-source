import json,os
D=os.path.dirname(os.path.abspath(__file__))
E0="pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;"
V="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
ARGS="let args=&(new,);"
SH="let r=(false,Some(args.0),true);"
STL="fee_configurable:a.global.creator_fee_configurable};let hopt=holder;"
STD="fee_configurable:bool}"
VS="fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
T="let t=if let Some(t)=new{t}else{"
def at_top(s): return (E0,E0+s)
V_={
 'v01':[at_top("let new=new;")],
 'v02':[(ARGS,""),at_top(ARGS)],
 'v03':[(V,V.replace(",new,",",args.0,"))],
 'v04':[(ARGS,""),at_top(ARGS),(V,V.replace(",new,",",args.0,"))],
 'v05':[(STD,"fee_configurable:bool,new:Option<Pubkey>}"),(STL,STL.replace("};",",new};")),(V,V.replace(",new,",",st.new,"))],
 'v06':[(STD,"fee_configurable:bool,new:Option<Pubkey>}"),(STL,STL.replace("};",",new};")),(V,V.replace(",new,",",st.new,")),(ARGS,""),(SH,SH.replace("args.0","st.new"))],
 'v07':[("struct CtoState{creator","struct CtoState{new:Option<Pubkey>,creator"),("let st=CtoState{creator","let st=CtoState{new,creator"),(V,V.replace(",new,",",st.new,"))],
 'v08':[at_top("let mut new=new;"),(ARGS,""),(SH,SH.replace("args.0","new.take()"))],
 'v09':[at_top("let new=new.map(|k|k);")],
 'v10':[at_top("let new=match new{Some(k)=>Some(k),None=>None};")],
 'v11':[(ARGS,"let args=(new,);")],
 'v12':[(VS,VS.replace("new:Option<Pubkey>","new:&Option<Pubkey>")),(T,T.replace("=new{","=*new{")),(V,V.replace(",new,",",&args.0,"))],
 'v13':[at_top("let (has_new,nk)=match new{Some(k)=>(true,k),None=>(false,Pubkey::default())};"),(ARGS,"let args=&(if has_new{Some(nk)}else{None},);"),(V,V.replace(",new,",",args.0,"))],
 'v14':[at_top("let mut new=new;"),(V,V.replace(",new,",",new.take(),"))],
}
for k,e in V_.items():
    open(f'{D}/{k}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V_))
