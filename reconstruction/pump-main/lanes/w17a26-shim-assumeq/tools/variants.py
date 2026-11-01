# VARIANTS[name] = [(lineno, old, new), ...] applied to $OUT/src/$MKBASE.rs (default main)
VARIANTS={
 'cal1':[(761,'let nf=a.bonding_curve.creator_fee_bps;','let nf=a.bonding_curve.creator_fee_bps;let c=nf==nf;unsafe{assume(c)}/*shim: calibration (neutral assume)*/;')],
}
VARIANTS['su1']=[(339,'if holder{sharing_update=Some(None);(false,false)}','if holder{sharing_update=Some(args.0);(false,false)}')]
VARIANTS['hu1']=[(755,'curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=_holder;')]
VARIANTS['hu2']=[(755,'curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward={let u=holder.unwrap_or(false);let c=u==_holder;unsafe{assume(c)}/*shim: assume unwrap_or(false)==hopt==Some(true)*/;u};')]
