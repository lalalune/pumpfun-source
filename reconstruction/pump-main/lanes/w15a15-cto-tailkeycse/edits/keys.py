# Tail key-binding spellings (w15a15 angle step 2). Each variant: list of (old,new) exact single-occurrence edits on
# programs/pump/src/creator/admin_cto.rs, line count preserved.
B0='let k0={let x:&AccountInfo=a.pool_authority.as_ref();x.key};'
B2='let k2={let x:&AccountInfo=a.global.as_ref().as_ref();x.key};'
E0=('key:x.key,executable:x.executable}},authority','key:k0,executable:x.executable}},authority')
E2=('rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}},mint:',
    'rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:k2}},mint:')
TOP='let a=&ctx.accounts;let mint'
MID='let signer_seeds:'
V={
 'k02top':[(TOP,'let a=&ctx.accounts;'+B0+B2+'let mint'),E0,E2],
 'k0top':[(TOP,'let a=&ctx.accounts;'+B0+'let mint'),E0],
 'k2top':[(TOP,'let a=&ctx.accounts;'+B2+'let mint'),E2],
 'k02mid':[(MID,B0+B2+MID),E0,E2],
 'k0mid':[(MID,B0+MID),E0],
}
