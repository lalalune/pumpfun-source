import json
CALL=("sweep(&ctx,&holder_key))","sweep(&ctx,&holder_key,&a.holder_creator_vault))")
SIG=("fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{","fn sweep<'info>(ctx:&Context<'_,'_,'_,'_,AdminCto<'info>>,holder_key:&Pubkey,hv:&AccountInfo<'info>)->Result<u64>{")
U1=("if a.holder_creator_vault.key()!=dest{","if hv.key()!=dest{")
U2=("with_pubkeys((a.holder_creator_vault.key(),dest))","with_pubkeys((hv.key(),dest))")
U3=("&a.admin_set_creator_authority,&a.holder_creator_vault)?","&a.admin_set_creator_authority,hv)?")
U4=("&a.creator_vault,&a.holder_creator_vault,amount","&a.creator_vault,hv,amount")
U5=("authority:a.holder_creator_vault.to_account_info()","authority:hv.to_account_info()")
TOP="let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
V={}
V['arg_all']=[CALL,SIG,U1,U2,U3,U4,U5]
V['arg_late']=[CALL,SIG,U3,U4,U5]
V['arg_cmp']=[CALL,SIG,U1,U2]
V['arg_native']=[CALL,SIG,U3,U4]
# binding inside sweep
B0=(TOP,"let a=&ctx.accounts;let hv=&a.holder_creator_vault;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;")
def ub(us): return [(x,y) for x,y in us]
V['bind_top_all']=[B0,U1,U2,U3,U4,U5]
V['bind_top_late']=[B0,U3,U4,U5]
# binding after dest check (in front of amm_frozen)
BA=("let amm_frozen=!a.coin_creator_vault_ata","let hv=&a.holder_creator_vault;let amm_frozen=!a.coin_creator_vault_ata")
V['bind_after_late']=[BA,U3,U4,U5]
# tuple dest carrier
TD=("let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;","let (dest,hv)=(Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0,&a.holder_creator_vault);")
V['tuple_dest_all']=[TD,U1,U2,U3,U4,U5]
V['tuple_dest_late']=[TD,U3,U4,U5]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
