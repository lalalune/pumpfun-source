# usage: gen.py SRC FRONT SECOND
import sys
src,front,second=sys.argv[1],sys.argv[2],sys.argv[3]
p=src+'/src/trade_v3.rs'; t=open(p).read()
F0="let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0; let post_buyback=match post{Some(p)=>crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0).0,None=>0};"
S0="let second=if let Some(p)=post{add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)?}else{0};"
B1="let buyback=if is_mayhem!=0{0}else{crate::protocol_fee_split(buyback_bps,protocol_fee,false).0};"
SP="crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,false).0"
FR={
 'p08': B1+" let post_buyback=match post{Some(p)=>if is_mayhem!=0{0}else{"+SP+"},None=>0};",
 'nonefirst': B1+" let post_buyback=match post{None=>0,Some(p)=>if is_mayhem!=0{0}else{"+SP+"}};",
 'guard': B1+" let post_buyback=match post{Some(p) if is_mayhem==0=>"+SP+",_=>0};",
 'iflet': B1+" let post_buyback=if let Some(p)=post{if is_mayhem!=0{0}else{"+SP+"}}else{0};",
 'or': B1+" let post_buyback=if is_mayhem!=0||post.is_none(){0}else{let p=post.unwrap();"+SP+"};",
 'nested': B1+" let post_buyback=if is_mayhem!=0{0}else{match post{Some(p)=>"+SP+",None=>0}};",
 'nestedinner': "let buyback=if is_mayhem!=0{0}else{crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0}; let post_buyback=match post{Some(p)=>if is_mayhem!=0{0}else{crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0).0},None=>0};",
}
SE={
 'iflet': S0,
 'some': "let second=match post{Some(p)=>add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)?,None=>0};",
 'none': "let second=match post{None=>0,Some(p)=>add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)?};",
 'isnone': "let second=if post.is_none(){0}else{let p=post.unwrap();add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)?};",
 'mapor': "let second=post.map_or(Ok(0),|p|add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee))?;",
}
assert t.count(F0)==1 and t.count(S0)==1
t=t.replace(F0,FR[front]).replace(S0,SE[second]); open(p,'w').write(t)
