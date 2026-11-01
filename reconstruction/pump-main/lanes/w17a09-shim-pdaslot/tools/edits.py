H0='let a=&ctx.accounts;let mint=a.mint.key();let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
PDA='Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)'
QL_TAIL='||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)'
E={}
# v1: scoped scratch block: PDA, sk and default key all in one MaybeUninit<[u64;5]>; scratch dies after quote_locked
E['v1']=[(H0,'let a=&ctx.accounts;let mint=a.mint.key();let holder_key:Pubkey;let shared;let quote_locked;{let mut scr=core::mem::MaybeUninit::<[u64;5]>::uninit();/*shim: orig -0x2d0 PDA/sk/default scratch*/unsafe{*scr.as_mut_ptr().cast::<(Pubkey,u8)>()='+PDA+';holder_key=core::mem::transmute(*scr.as_ptr().cast::<[u64;4]>());}/*shim: PDA into the scratch, holder_key read back as [u64;4]*/shared=unsafe{*scr.as_mut_ptr().cast::<Pubkey>()=a.sharing_config.key();a.bonding_curve.creator==*scr.as_ptr().cast::<Pubkey>()}/*shim: sk in the scratch*/&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{*scr.as_mut_ptr().cast::<Pubkey>()=Pubkey::default();q==*scr.as_ptr().cast::<Pubkey>()})/*shim: default key in the scratch*/'+QL_TAIL+'};}')]
# v2: same but scratch lives for the whole function (no block)
E['v2']=[(H0,'let a=&ctx.accounts;let mint=a.mint.key();let mut scr=core::mem::MaybeUninit::<[u64;5]>::uninit();/*shim: orig -0x2d0 PDA/sk/default scratch*/let holder_key:Pubkey=unsafe{*scr.as_mut_ptr().cast::<(Pubkey,u8)>()='+PDA+';core::mem::transmute(*scr.as_ptr().cast::<[u64;4]>())}/*shim: PDA into the scratch, holder_key read back as [u64;4]*/;let shared=unsafe{*scr.as_mut_ptr().cast::<Pubkey>()=a.sharing_config.key();a.bonding_curve.creator==*scr.as_ptr().cast::<Pubkey>()}/*shim: sk in the scratch*/&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{*scr.as_mut_ptr().cast::<Pubkey>()=Pubkey::default();q==*scr.as_ptr().cast::<Pubkey>()})/*shim: default key in the scratch*/'+QL_TAIL+'};')]
# v3: plain PDA-first, short-lived temp (control: hk dies at once) ; sk/default untouched
E['v3']=[(H0,'let a=&ctx.accounts;let mint=a.mint.key();let holder_key='+PDA+'.0;let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()'+QL_TAIL+'};')]
# v4: PDA-first keeping hk alive (main's binding form, just moved first)
E['v4']=[(H0,'let a=&ctx.accounts;let mint=a.mint.key();let holder_key;let hk='+PDA+';holder_key=hk.0;let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()'+QL_TAIL+'};')]
SH='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
QL='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()'+QL_TAIL+'};'
HKS='let holder_key:Pubkey;let mut hk=core::mem::MaybeUninit::<[u64;5]>::uninit();/*shim: 8-aligned 40 B PDA result scratch (orig -0x2d0 shape)*/unsafe{*hk.as_mut_ptr().cast::<(Pubkey,u8)>()='+PDA+';holder_key=core::mem::transmute(*hk.as_ptr().cast::<[u64;4]>())}/*shim: holder_key read back as [u64;4] (orig 4 aligned ldxdw/stxdw)*/;'
HKSb='let holder_key:Pubkey;let mut hk=core::mem::MaybeUninit::<[u64;5]>::uninit();/*shim: 8-aligned 40 B PDA result scratch (orig -0x2d0 shape)*/unsafe{*hk.as_mut_ptr().cast::<(Pubkey,u8)>()='+PDA+';holder_key=*hk.as_ptr().cast::<Pubkey>()}/*shim: holder_key read back from the scratch*/;'
HEAD='let a=&ctx.accounts;let mint=a.mint.key();'
E['v5']=[(H0,HEAD+SH+HKS+QL)]
E['v5b']=[(H0,HEAD+SH+HKSb+QL)]
E['v6']=[(H0,HEAD+HKS+SH+QL)]
E['v6b']=[(H0,HEAD+HKSb+SH+QL)]
# v7: holder_key lives in a 72 B MaybeUninit (key at +0, 40 B tail = hk's old frame region), PDA result is a short-lived temp (merges into orig -0x2d0 host)
HK72='let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();/*shim: holder_key in a 72 B slot whose 40 B tail keeps hk\'s frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkx.as_mut_ptr().cast::<Pubkey>().write('+PDA+'.0);&*hkx.as_ptr().cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;'
USES=[('validate(&st,hopt,fee,new,&holder_key,&sk)','validate(&st,hopt,fee,new,holder_key,&sk)'),('sweep(&ctx,&holder_key)','sweep(&ctx,holder_key)')]
E['v7']=[(H0,HEAD+SH+HK72+QL)]+USES
E['v8']=[(H0,HEAD+HK72+SH+QL)]+USES
# v9 (= IR e1ab): PDA-first 72 B holder_key slot + sharing_config AccountInfo ptr read (volatile) before the PDA and reused for sk/owner/data_is_empty
SC='let sc:&AccountInfo=unsafe{&**(&a.sharing_config as *const UncheckedAccount as *const *const AccountInfo).cast::<&AccountInfo>()};'
SCV='let sc:&AccountInfo=unsafe{&*core::ptr::read_volatile(&a.sharing_config as *const UncheckedAccount as *const *const AccountInfo)};/*shim: sharing_config AccountInfo ptr read before the PDA (greedy RA keeps r8 for accounts)*/'
SH9='let shared={let sk=*sc.key;a.bonding_curve.creator==sk}&&sc.owner==&FEES&&!sc.data_is_empty();'
E['v9']=[(H0,HEAD+SCV+HK72+SH9+QL)]+USES
QLV='let quote_locked={let q=unsafe{(*core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const Account<BondingCurve>)).quote_mint}/*shim: curve ptr re-read after the shared test (no PRE across E1)*/;q==Pubkey::default()'+QL_TAIL+'};'
E['v10']=[(H0,HEAD+SCV+HK72+SH9+QLV)]+USES
E['v11']=[(H0,HEAD+HK72+SH+QLV)]+USES
