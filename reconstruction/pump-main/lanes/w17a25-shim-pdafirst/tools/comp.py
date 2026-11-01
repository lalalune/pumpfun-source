# components: name -> list of (old,new). Used by mk.py to build edit files.
SH='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&unsafe{&*(ptp(23,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
SHV='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&unsafe{core::ptr::read_volatile(&a.sharing_config)}.owner==&FEES/*shim: fresh sharing_config load per use (keeps accounts in r8 under PDA-first)*/&&!unsafe{core::ptr::read_volatile(&a.sharing_config)}.data_is_empty();'
PDA='let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();/*shim: holder_key in a 72 B slot whose 40 B tail keeps hk\'s frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkx.as_mut_ptr().cast::<Pubkey>().write(Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0);&*hkx.as_ptr().cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;'
VR='unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}'
C={}
C['k8']=[(SH+PDA,PDA+SH)]
C['pf9v']=[(SH+PDA,PDA+SHV)]
T1H='(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('
C['FT']=[(T1H,'(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){let a='+VR+'/*shim: fresh accounts pointer at the TCF clone-run head (RA firewall)*/;crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(')]
C1H='const _: [();core::mem::align_of::<Program<\'static,crate::legacy_sell::LegacyFeesProgram>>()]=[();core::mem::align_of::<&\'static AccountInfo<\'static>>()];crate::pump_fees::cpi::admin_cto_sharing_config('
C['FC']=[(C1H,C1H.replace('crate::pump_fees::cpi::admin_cto_sharing_config(','let a='+VR+'/*shim: fresh accounts pointer at the sharing clone-run head (RA firewall)*/;crate::pump_fees::cpi::admin_cto_sharing_config('))]
# passthrough forms
def PTP(n): return 'unsafe{&*(ptp('+str(n)+',&**a as *const AdminCto as *const u8) as *const AdminCto)}'
C['PT']=[(T1H,'(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){let a='+PTP(40)+'/*shim: passthrough accounts pointer at the TCF clone-run head*/;crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(')]
C['PC']=[(C1H,C1H.replace('crate::pump_fees::cpi::admin_cto_sharing_config(','let a='+PTP(41)+'/*shim: passthrough accounts pointer at the sharing clone-run head*/;crate::pump_fees::cpi::admin_cto_sharing_config('))]
VRC='unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(&ctx.accounts))}'
C['FE']=[('let quote_locked={','let a='+VR+'/*shim: fresh accounts pointer after the entry block (RA firewall)*/;let quote_locked={')]
C['FJ']=[('crate::trade_types::prepare_bonding_curve(','let a='+VR+'/*shim: fresh accounts pointer at the join (RA firewall)*/;crate::trade_types::prepare_bonding_curve(')]
C['FW']=[('fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;','fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a='+VRC+'/*shim: fresh accounts pointer at the wallet head (RA firewall)*/;')]
C['FS']=[('fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;','fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a='+VRC+'/*shim: fresh accounts pointer at the sweep head (RA firewall)*/;')]
C['FE']=[('let quote_locked={','let a2:&AdminCto='+VR+'/*shim: fresh accounts pointer after the entry block (RA firewall)*/;let a=&a2;let quote_locked={')]
C['FE2']=[('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let a2:&AdminCto='+VR+'/*shim: fresh accounts pointer after quote_locked (RA firewall)*/;let a=&a2;let (_holder,cashback,target,sharing_update,collect_old,skip)={')]
C['FE4']=[('let mut sharing_update:Option<Option<Pubkey>>=None;','let a2:&AdminCto='+VR+'/*shim: fresh accounts pointer after validate (RA firewall)*/;let a=&a2;let mut sharing_update:Option<Option<Pubkey>>=None;')]
RS='{let a=unsafe{&*core::ptr::read_volatile(hkp.add(4))}/*shim: per-clone accounts reload from the manual hkx-tail slot*/;'
C['MSst']=[('let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();','let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();let hkp=hkx.as_mut_ptr() as *mut *const AdminCto;'),
           ('let quote_locked={','unsafe{core::ptr::write_volatile(hkp.add(4),&**a as *const AdminCto)}/*shim: accounts pointer kept in the hkx tail (manual spill slot)*/;let quote_locked={')]
_c1=[('CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{','CpiContext::new_with_signer('+RS+'a.pump_fees.to_account_info()},crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{'),
     ('pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();','pool_authority:'+RS+'let x:&AccountInfo= a.pool_authority.as_ref();'),
     ('authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();','authority:'+RS+'let x:&AccountInfo=a.admin_set_creator_authority.as_ref();'),
     ('global:{let x:&AccountInfo= a.global.as_ref().as_ref();','global:'+RS+'let x:&AccountInfo= a.global.as_ref().as_ref();'),
     ('mint:{let x:&AccountInfo= a.mint.as_ref();','mint:'+RS+'let x:&AccountInfo= a.mint.as_ref();'),
     ('sharing_config:{let x:&AccountInfo=a.sharing_config.as_ref();','sharing_config:'+RS+'let x:&AccountInfo=a.sharing_config.as_ref();'),
     ('event_authority:AccountInfo{data:ead,','event_authority:'+RS+'AccountInfo{data:ead,'),
     ('executable:a.pump_fees_event_authority.executable},program:{let x:&AccountInfo=a.pump_fees.as_ref();','executable:a.pump_fees_event_authority.executable}},program:'+RS+'let x:&AccountInfo=a.pump_fees.as_ref();')]
C['MSc1']=_c1
RS2='{let a=unsafe{&**hkp.add(4)}/*shim: per-clone accounts reload from the manual hkx-tail slot*/;'
C['MSc1n']=[(o,n.replace(RS,RS2)) for o,n in _c1]
C['MSstn']=[C['MSst'][0],('let quote_locked={','unsafe{*hkp.add(4)=&**a as *const AdminCto}/*shim: accounts pointer kept in the hkx tail (manual spill slot)*/;let quote_locked={')]
RT='{let a=unsafe{&**hkp.add(4)}/*shim: accounts reload from the manual hkx-tail slot (orig reload site)*/;'
C['MShk']=[('fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;','fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let hkp=holder_key as *const Pubkey as *const *const AdminCto;')]
C['MSt1cv']=[('pump_creator_vault:a.creator_vault.to_account_info(),','pump_creator_vault:'+RT+'a.creator_vault.to_account_info()},')]
C['MSt1ep']=[('event_authority:a.pump_amm_event_authority.to_account_info(),program:{let x:&AccountInfo=a.pump_amm.as_ref();','event_authority:'+RT+'a.pump_amm_event_authority.to_account_info()},program:'+RT+'let x:&AccountInfo=a.pump_amm.as_ref();')]
LT='/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/'
C['ANN']=[(LT,LT+'extern "C"{#[link_name="llvm.ptr.annotation.p0.p0"]fn pann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8)->*const u8;}/*shim: llvm.ptr.annotation = identity call dropped at ISel (no instruction)*/')]
PA='unsafe{&*(pann(&**a as *const AdminCto as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null()) as *const AdminCto)}'
C['PAT']=C['ANN']+[(T1H,'(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){let a='+PA+'/*shim: annotated accounts pointer at the TCF clone-run head (RA firewall)*/;crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(')]
C['PAC']=[(C1H,C1H.replace('crate::pump_fees::cpi::admin_cto_sharing_config(','let a='+PA+'/*shim: annotated accounts pointer at the sharing clone-run head (RA firewall)*/;crate::pump_fees::cpi::admin_cto_sharing_config('))]
C['PAS']=[('fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;','fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let a='+PA+'/*shim: annotated accounts pointer at the sweep head (RA firewall)*/;')]
C['PAE4']=[('let mut sharing_update:Option<Option<Pubkey>>=None;','let a2:&AdminCto='+PA+'/*shim: annotated accounts pointer after validate (RA firewall)*/;let a=&a2;let mut sharing_update:Option<Option<Pubkey>>=None;')]
C['F0']=[('let shared={','let a2:&AdminCto='+VR+'/*shim: fresh accounts pointer before the shared test (RA firewall)*/;let a=&a2;let shared={')]
C['PA0']=C['ANN']+[('let shared={','let a2:&AdminCto='+PA+'/*shim: annotated accounts pointer before the shared test (RA firewall)*/;let a=&a2;let shared={')]
