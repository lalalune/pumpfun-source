# stitch13 genes: stitch12 library + w14a89 t-family
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes as _G
G=_G.G
def apply(s,names): return _G.apply(s,names)
_T0='if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{'
G['t1']=[('if shared{if holder{(false,Some(None),false)}else{','if shared{if new.is_none(){(false,Some(None),false)}else{')]
G['t3']=[('if shared{if holder{(false,Some(None),false)}else{','if shared{if let None=new{(false,Some(None),false)}else{')]
G['t4']=[(_T0,'if shared{if new.is_some(){let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}else{(false,Some(None),false)}}else{')]
G['t5']=[(_T0,'if shared{match new{None=>(false,Some(None),false),Some(_)=>{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}}else{')]
# size-knob catalog (sizeknobs-cto.json) as genes K_<name>
import json as _j
for _k in _j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    _n='K_'+_k['name']
    if _n not in G and _k.get('edit'): G[_n]=[(e['old'],e['new']) for e in _k['edit']]
# entry spellings of the shared test (t1 fill candidates; junk bound t1+16 B at entry 0x140-0x190 = +1)
_SC="&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let holder_key;"
G['en_dlen']=[(_SC,"&&a.sharing_config.owner==&FEES&&a.sharing_config.data_len()!=0;let holder_key;")]
G['en_dlen_gt']=[(_SC,"&&a.sharing_config.owner==&FEES&&a.sharing_config.data_len()>0;let holder_key;")]
G['en_ownd']=[(_SC,"&&*a.sharing_config.owner==FEES&&!a.sharing_config.data_is_empty();let holder_key;")]
G['en_feesl']=[(_SC,"&&&FEES==a.sharing_config.owner&&!a.sharing_config.data_is_empty();let holder_key;")]
