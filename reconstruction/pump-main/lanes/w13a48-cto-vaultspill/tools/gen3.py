CALL=("sweep(&ctx,&holder_key))",None)
SIG0="fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{"
TOP="let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
BUMP="let bump=ctx.bumps.creator_vault;"
V={}
# b1: bump passed as u8 arg from execute
V['bumparg']=[("sweep(&ctx,&holder_key))","sweep(&ctx,&holder_key,ctx.bumps.creator_vault))"),(SIG0,"fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,bump:u8)->Result<u64>{"),("1];"+BUMP,"1];")]
# pad: removing BUMP shortens line - fine (no newline change)
# b2: native passed as bool arg from execute
V['nativearg']=[("sweep(&ctx,&holder_key))","sweep(&ctx,&holder_key,a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID))"),(SIG0,"fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,native:bool)->Result<u64>{"),(TOP,"let a=&ctx.accounts;")]
# b3: bump read at sweep top
V['bumptop']=[(TOP,"let a=&ctx.accounts;let bump=ctx.bumps.creator_vault;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"),("1];"+BUMP,"1];")]
# b4: bump read right after dest check
V['bumpafterdest']=[("let amm_frozen=!a.coin_creator_vault_ata","let bump=ctx.bumps.creator_vault;let amm_frozen=!a.coin_creator_vault_ata"),("1];"+BUMP,"1];")]
# b5: native computed after dest check
V['nativeafterdest']=[(TOP,"let a=&ctx.accounts;"),("let amm_frozen=!a.coin_creator_vault_ata","let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;let amm_frozen=!a.coin_creator_vault_ata")]
# b6: bump + native both as args
V['bothargs']=[("sweep(&ctx,&holder_key))","sweep(&ctx,&holder_key,a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID,ctx.bumps.creator_vault))"),(SIG0,"fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,native:bool,bump:u8)->Result<u64>{"),(TOP,"let a=&ctx.accounts;"),("1];"+BUMP,"1];")]
for k,v in V.items(): open(k+'.py','w').write('EDITS='+repr(v)+'\n')
