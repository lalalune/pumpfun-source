# w16a04 lanchorceil genes: w15a32 genes_lbw (w15a16 genes_mp + stitch15) plus the composite leads named by the angle.
# Experiment only. Each gene is a list of exact single-occurrence (old,new) replacements; line count must hold.
import os,sys,runpy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_lbw as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
_E=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'e')
# c2 (w15a24 edits/c2.py): TCF pump_creator_vault_ata clone lamports-first, all fields via x (derive order)
G['c2']=[("pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),",
          "pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,")]
# s1 (w14a85 edits/gen.py, regenerated on this base into e/s1.py): all AdminCtoSharingConfig fields as to_account_info()
if os.path.exists(_E+'/s1.py'): G['s1']=list(runpy.run_path(_E+'/s1.py')['EDITS'])
# tf_g1a (w15a21 tg.py): let creator=st.creator before args, target=creator first in the shared non-holder arm
_NA="else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}"
G['tf_g1a']=[("let args=&(new,);","let creator=st.creator;let args=&(new,);"),(_NA,"else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
G['g0']=[(_NA,"else{sharing_update=Some(args.0);target=st.creator;(false,true)}}")]
# n1 (w15a04 edits/_n1.py): no nf local; the event reads a.bonding_curve.creator_fee_bps
G['n1']=[("let nf=a.bonding_curve.creator_fee_bps;","                                      "),("new_creator_fee_bps:nf,","new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")]
# po (w15a04 _po.py): owner-first pool gate (original order)
G['po']=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();")]
