# source variants on main 8330455eb (line 339 only; line count kept). Experiment only.
SH='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&unsafe{&*(ptp(23,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
HK72="let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();/*shim: holder_key in a 72 B slot whose 40 B tail keeps hk's frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkx.as_mut_ptr().cast::<Pubkey>().write(Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID).0);&*hkx.as_ptr().cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;"
QL='let quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{expect(q==Pubkey::default(),false)})/*shim: default-quote test weighted 1:2000*/||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
ST='let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,max_fee:unsafe{&*(ptp(24,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of max_fee*/.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};'
VAL='let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;'
K8=('cto',SH+HK72,HK72+SH)
G='let g:&Account<Global>=unsafe{core::ptr::read_volatile(&a.global as *const Box<Account<Global>> as *const &Account<Global>)}/*shim: global ptr loaded once, before the curve flags (orig r6 at +0x288)*/;'
EF='let (cb0,hr0,my0)=unsafe{(core::ptr::read_volatile(&a.bonding_curve.is_cashback_coin),core::ptr::read_volatile(&a.bonding_curve.is_holder_reward),core::ptr::read_volatile(&a.bonding_curve.is_mayhem_mode))}/*shim: curve flags read before the quote-mint copy, orig order a3,a5,a2*/;'
QLG=QL.replace('a.global.whitelisted_quote_mints','g.whitelisted_quote_mints')
WV='core::ptr::write_volatile(core::ptr::addr_of_mut!((*p).%s),%s);'
def stv(gl,hoist=True):
    loads=('let (mf0,he0,fc0)=(%s.max_configurable_creator_fee_bps,%s.is_holder_reward_enabled,%s.creator_fee_configurable);'%(gl,gl,gl)) if hoist else ''
    mf,he,fc=('mf0','he0','fc0') if hoist else (gl+'.max_configurable_creator_fee_bps',gl+'.is_holder_reward_enabled',gl+'.creator_fee_configurable')
    return ('let mut stu=core::mem::MaybeUninit::<CtoState>::uninit();let st=unsafe{let p=stu.as_mut_ptr();'+loads
     +WV%('cashback','cb0')+WV%('holder_reward','hr0')+WV%('mayhem','my0')
     +'core::ptr::addr_of_mut!((*p).creator).write(a.bonding_curve.creator);'
     +WV%('quote_locked','quote_locked')+WV%('fee_configurable',fc)+WV%('holder_enabled',he)+WV%('max_fee',mf)
     +'stu.assume_init_ref()}/*shim: orig stxb order -0xe,-0xf,-0x10 | creator | -0xd,-0xb,-0xc | max_fee*/;')
VALR=('cto',VAL,'let mut target=validate(st,hopt,fee,new,holder_key,&sk)?;')
V={'m1':[]}
V['k8']=[K8]
V['sh1h']=[('cto',QL,G+EF+QLG),('cto',ST,stv('g')),VALR]
V['sh1']=[('cto',QL,EF+QL),('cto',ST,stv('a.global',hoist=False)),VALR]
V['sh1hk8']=[K8,('cto',QL,G+EF+QLG),('cto',ST,stv('g')),VALR]
# sh1h2: plain early reads (keep !range, no and-1), plain early global binding, creator by raw-place assignment (memcpy, not memmove)
G2='let g:&Account<Global>=&a.global;'
EF2='let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'
def stv2(gl):
    return ('let mut stu=core::mem::MaybeUninit::<CtoState>::uninit();let st=unsafe{let p=stu.as_mut_ptr();'
     +'let (mf0,he0,fc0)=(%s.max_configurable_creator_fee_bps,%s.is_holder_reward_enabled,%s.creator_fee_configurable);'%(gl,gl,gl)
     +WV%('cashback','cb0')+WV%('holder_reward','hr0')+WV%('mayhem','my0')
     +'(*p).creator=a.bonding_curve.creator;'
     +WV%('quote_locked','quote_locked')+WV%('fee_configurable','fc0')+WV%('holder_enabled','he0')+WV%('max_fee','mf0')
     +'stu.assume_init_ref()}/*shim: orig stxb order -0xe,-0xf,-0x10 | creator | -0xd,-0xb,-0xc | max_fee*/;')
V['sh1h2']=[('cto',QL,G2+EF2+QLG),('cto',ST,stv2('g')),VALR]
V['sh1h2k8']=[K8,('cto',QL,G2+EF2+QLG),('cto',ST,stv2('g')),VALR]
