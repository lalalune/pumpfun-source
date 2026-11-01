#![no_std]
#![feature(core_intrinsics, link_llvm_intrinsics)]
extern "C" { #[link_name="llvm.expect.i1"] fn expect(b: bool, v: bool) -> bool; }
extern "C" { #[link_name="llvm.expect.with.probability.i1"] fn expect_p(b: bool, v: bool, p: f64) -> bool; }
extern "C" { fn g(x: u64) -> u64; fn h(x: u64) -> u64; fn k(x: u64) -> u64; }
// f1: core::intrinsics::unlikely -> no !prof (result goes through an alloca before LowerExpectIntrinsic)
#[no_mangle] pub fn f1(x: u64) -> u64 { if core::intrinsics::unlikely(x == 5) { unsafe{g(x)} } else { unsafe{h(x+1)} } }
// f2: extern llvm.expect.i1 -> branch_weights 1:2000
#[no_mangle] pub fn f2(x: u64) -> u64 { if unsafe{expect(x == 6, false)} { unsafe{g(x+2)} } else { unsafe{h(x+3)} } }
// f3: #[cold] call -> no !prof after cold() is inlined (inliner-time only)
#[cold] fn cold(){}
#[no_mangle] pub fn f3(x: u64) -> u64 { if x == 7 { cold(); unsafe{g(x+4)} } else { unsafe{k(x+5)} } }
// f4: extern llvm.expect.with.probability.i1 -> any ratio (0.6667 -> 1431727348:715756301 = 2:1)
#[no_mangle] pub fn f4(x: u64) -> u64 { if unsafe{expect_p(x == 8, true, 0.6667)} { unsafe{g(x+6)} } else { unsafe{h(x+7)} } }
