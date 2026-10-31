# w14a119 genes: stitch13 library + inline-L339-6
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s13 as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
G['I6']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=a.bonding_curve.creator;(false,Some(args.0),true)')]
G['I6p']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=a.bonding_curve.creator;((false,Some(args.0),true))')]
G['I6s']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=st.creator;(false,Some(args.0),true)')]
import mine108 as _M
for _n,_e in _M.G.items(): G['m_'+_n]=_e
G['I6sn']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=st.creator;(false,Some(new),true)')]
G['I6b']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=a.bonding_curve.creator;let r=(false,Some(args.0),true);r')]
G['I6sb']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=st.creator;let r=(false,Some(args.0),true);r')]
G['I6sa']=[('let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r','target=st.creator;(false,Some(args.0),true)')]
G['T1s']=[('if shared{if holder{(false,Some(None),false)}else{','if shared{if new.is_none(){(false,Some(None),false)}else{')]
G['T3s']=[('if shared{if holder{(false,Some(None),false)}else{','if shared{if let None=new{(false,Some(None),false)}else{')]
G['Hsw']=[('if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}','if shared{if !holder{target=st.creator;(false,Some(args.0),true)}else{(false,Some(None),false)}}')]
G['Hsw6']=[('if shared{if holder{(false,Some(None),false)}else{target=a.bonding_curve.creator;(false,Some(args.0),true)}}','if shared{if !holder{target=a.bonding_curve.creator;(false,Some(args.0),true)}else{(false,Some(None),false)}}')]
