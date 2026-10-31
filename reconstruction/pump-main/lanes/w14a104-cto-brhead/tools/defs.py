L289=' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
L296=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'
L298=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
E289='return Err(error!(PumpError::HolderRewardCreatorImmutable));'
E296='return Err(error!(PumpError::HolderRewardDisabled));'
E298='return Err(error!(PumpError::CtoNewCreatorNotAllowed));'
V={}
V['nest289']=[(L289,' if st.holder_reward{if !holder{'+E289+'}}')]
V['h289']=[(L289,' if st.holder_reward&&!holder{'+E289+'}')]
V['nest296']=[(L296,' if holder{if !st.holder_reward&&!st.holder_enabled{'+E296+'}}')]
V['in298']=[(L296+'\n\n'+L298,' let target=if holder{if !st.holder_reward&&!st.holder_enabled{'+E296+'}\n\n  if new.is_some(){'+E298+'}*holder_key}else{')]
V['mtup']=[(L289,' match (st.holder_reward,holder){(true,false)=>{'+E289+'}'),(L296,' (false,true)=>{if !st.holder_enabled{'+E296+'}}_=>{}}')]
V['mhold']=[(L289,' match holder{false=>{if st.holder_reward{'+E289+'}}'),(L296,' true=>{if !st.holder_reward&&!st.holder_enabled{'+E296+'}}}')]
V['mhold_t']=[(L289,' match holder{true=>{}false=>{if st.holder_reward{'+E289+'}}}'),(L296,' if holder&&!st.holder_reward&&!st.holder_enabled{'+E296+'}')]
V['s289G']=[(L289,' if st.holder_reward&&!(hopt==Some(true)){Err(error!(PumpError::HolderRewardCreatorImmutable))}else{Ok(())}?;')]
V['m289opt']=[(L289,' if st.holder_reward{match hopt{Some(true)=>{}_=>{'+E289+'}}}')]
V['mhr']=[(L289,' match st.holder_reward{true=>{if !holder{'+E289+'}}'),(L296,' false=>{if holder&&!st.holder_enabled{'+E296+'}}}')]
V['letelse298']=[(L298,' let target=if holder{let None=new else{'+E298+'};*holder_key}else{')]
V['ne289']=[(L289,' if st.holder_reward&&hopt!=Some(true){'+E289+'}')]
def get(name):
    E=[]
    for n in name.split('+'): E+=V[n]
    return E
def r296(c): return [(L296,' if '+c+'{'+E296+'}')]
V['o1']=r296('!st.holder_reward&&holder&&!st.holder_enabled')
V['o2']=r296('holder&&!(st.holder_reward||st.holder_enabled)')
V['o3']=r296('!(st.holder_reward||st.holder_enabled)&&holder')
V['o4']=r296('holder&&!st.holder_enabled&&!st.holder_reward')
V['o5']=r296('hopt==Some(true)&&!st.holder_reward&&!st.holder_enabled')
V['o6']=r296('!st.holder_reward&&!st.holder_enabled&&holder')
V['o7']=r296('holder&&!st.holder_reward&&!st.holder_enabled&&true')
V['o8']=r296('holder&&!(st.holder_reward|st.holder_enabled)')
V['o9']=r296('holder&!st.holder_reward&!st.holder_enabled')
import sys as _s, os as _o
_s.path.insert(0,_o.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a104-cto-brhead/e'))
import gen as _gen
SRC=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a104-cto-brhead/programs/pump/src/creator/admin_cto.rs').read()
def get(name):
    E=[]; s=SRC
    for n in name.split('+'):
        e=V[n] if n in V else _gen.mk(n,s)
        for a,b in e:
            assert s.count(a)==1,(n,a[:100]); s=s.replace(a,b)
        E+=e
    return E
_T306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
V['le306']=[(_T306,'let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
L312E='{return Err(error!(PumpError::InvalidCreator));}t};'
V['t298m']=[(L298,' let target=match hopt{Some(true)=>{if new.is_some(){'+E298+'}*holder_key}_=>{'),(L312E,'{return Err(error!(PumpError::InvalidCreator));}t}};')]
V['t298m2']=[(L298,' let target=match hopt{Some(false)|None=>{'),(L312E,'{return Err(error!(PumpError::InvalidCreator));}t}Some(true)=>{if new.is_some(){'+E298+'}*holder_key}};')]
V['t298h']=[(L298,' let target=if hopt==Some(true){if new.is_some(){'+E298+'}*holder_key}else{')]
V['t298n']=[(L298,' let target=if !holder{'),(L312E,'{return Err(error!(PumpError::InvalidCreator));}t}else{if new.is_some(){'+E298+'}*holder_key};')]
_VH='->Result<Pubkey>{let holder=hopt==Some(true);'
def vh(e): return [(_VH,'->Result<Pubkey>{let holder='+e+';')]
V['vu']=vh('hopt.unwrap_or(false)')
V['vm']=vh('matches!(hopt,Some(true))')
V['vsa']=vh('hopt.is_some_and(|h|h)')
V['vil']=vh('if let Some(h)=hopt{h}else{false}')
V['vud']=vh('hopt.unwrap_or_default()')
V['u298']=[(L298,' let target=if hopt.unwrap_or(false){if new.is_some(){'+E298+'}*holder_key}else{')]
_C296=' let hold=||->Result<Pubkey>{if !st.holder_reward&&!st.holder_enabled{'+E296+'}'
_C298='  if new.is_some(){'+E298+'}Ok(*holder_key)};'
_F296=' fn hold(st:&CtoState,new:&Option<Pubkey>,holder_key:&Pubkey)->Result<Pubkey>{if !st.holder_reward&&!st.holder_enabled{'+E296+'}'
_F298='  if new.is_some(){'+E298+'}Ok(*holder_key)}'
V['clp']=[(L296,_C296),(L298,_C298+'let target=if holder{hold()?}else{')]
V['cln']=[(L296,_C296),(L298,_C298+'let target=if !holder{'),(L312E,'{return Err(error!(PumpError::InvalidCreator));}t}else{hold()?};')]
V['fnp']=[(L296,_F296),(L298,_F298+'let target=if holder{hold(st,&new,holder_key)?}else{')]
V['fnn']=[(L296,_F296),(L298,_F298+'let target=if !holder{'),(L312E,'{return Err(error!(PumpError::InvalidCreator));}t}else{hold(st,&new,holder_key)?};')]
V['m2']=[]
