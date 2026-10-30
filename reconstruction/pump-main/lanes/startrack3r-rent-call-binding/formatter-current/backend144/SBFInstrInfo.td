//===-- SBFInstrInfo.td - Target Description for SBF Target ---------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file describes the SBF instructions in TableGen format.
//
//===----------------------------------------------------------------------===//

include "SBFInstrFormats.td"
include "SBFTargetFeatures.td"

// Instruction Operands and Patterns

// These are target-independent nodes, but have target-specific formats.
def SDT_SBFCallSeqStart : SDCallSeqStart<[SDTCisVT<0, iPTR>,
                                          SDTCisVT<1, iPTR>]>;
def SDT_SBFCallSeqEnd   : SDCallSeqEnd<[SDTCisVT<0, iPTR>, SDTCisVT<1, iPTR>]>;
def SDT_SBFCall         : SDTypeProfile<0, -1, [SDTCisVT<0, iPTR>]>;
def SDT_SBFSetFlag      : SDTypeProfile<0, 3, [SDTCisSameAs<0, 1>]>;
def SDT_SBFSelectCC     : SDTypeProfile<1, 5, [SDTCisSameAs<1, 2>,
                                               SDTCisSameAs<0, 4>,
                                               SDTCisSameAs<4, 5>]>;
def SDT_SBFBrCC         : SDTypeProfile<0, 4, [SDTCisSameAs<0, 1>,
                                               SDTCisVT<3, OtherVT>]>;
def SDT_SBFWrapper      : SDTypeProfile<1, 1, [SDTCisSameAs<0, 1>,
                                               SDTCisPtrTy<0>]>;

def SBFcall         : SDNode<"SBFISD::CALL", SDT_SBFCall,
                             [SDNPHasChain, SDNPOptInGlue, SDNPOutGlue,
                              SDNPVariadic]>;
def SBFretglue     : SDNode<"SBFISD::RET_GLUE", SDTNone,
                             [SDNPHasChain, SDNPOptInGlue, SDNPVariadic]>;
def SBFcallseq_start: SDNode<"ISD::CALLSEQ_START", SDT_SBFCallSeqStart,
                             [SDNPHasChain, SDNPOutGlue]>;
def SBFcallseq_end  : SDNode<"ISD::CALLSEQ_END",   SDT_SBFCallSeqEnd,
                             [SDNPHasChain, SDNPOptInGlue, SDNPOutGlue]>;
def SBFbrcc         : SDNode<"SBFISD::BR_CC", SDT_SBFBrCC,
                             [SDNPHasChain, SDNPOutGlue, SDNPInGlue]>;

def SBFselectcc     : SDNode<"SBFISD::SELECT_CC", SDT_SBFSelectCC, [SDNPInGlue]>;
def SBFWrapper      : SDNode<"SBFISD::Wrapper", SDT_SBFWrapper>;
def SBFIsLittleEndian : Predicate<"CurDAG->getDataLayout().isLittleEndian()">;
def SBFIsBigEndian    : Predicate<"!CurDAG->getDataLayout().isLittleEndian()">;
def SBFHasALU32 : Predicate<"Subtarget->getHasAlu32()">;
def SBFNoALU32 : Predicate<"!Subtarget->getHasAlu32()">;
def SBFHasLddw : Predicate<"!Subtarget->getNoLddw()">;
def SBFNoLddw : Predicate<"Subtarget->getNoLddw()">;
def SBFHasNeg : Predicate<"!Subtarget->getDisableNeg()">;
def SBFNoNeg: Predicate<"Subtarget->getDisableNeg()">;
def SBFRevSub : Predicate<"Subtarget->getReverseSubImm()">;
def SBFNoRevSub : Predicate<"!Subtarget->getReverseSubImm()">;
def SBFCallxSrc : Predicate<"Subtarget->getCallXRegSrc()">, AssemblerPredicate<(all_of FeatureCallxRegSrc)>;
def SBFNoCallxSrc : Predicate<"!Subtarget->getCallXRegSrc()">;
def SBFPqrInstr : Predicate<"Subtarget->getHasPqrClass()">;
def SBFNoPqrInstr : Predicate<"!Subtarget->getHasPqrClass()">;
def SBFHasStoreImm : Predicate<"Subtarget->getHasStoreImm()">;
def SBFExplicitSignExt : Predicate<"Subtarget->getHasExplicitSignExt()">;
def SBFNoExplicitSignExt : Predicate<"!Subtarget->getHasExplicitSignExt()">;
def SBFNewMemEncoding : Predicate<"Subtarget->getNewMemEncoding()">, AssemblerPredicate<(all_of FeatureNewMemEncoding)>;
def SBFOldMemEncoding : Predicate<"!Subtarget->getNewMemEncoding()">;
def SBFHasStaticSyscalls : Predicate<"Subtarget->getHasStaticSyscalls()">;
def SBFNoStaticSyscalls : Predicate<"!Subtarget->getHasStaticSyscalls()">;

def brtarget : Operand<OtherVT> {
  let PrintMethod = "printBrTargetOperand";
}
def calltarget : Operand<i64>;

def u64imm   : Operand<i64> {
  let PrintMethod = "printImm64Operand";
}

def gpr_or_imm : Operand<i64>;

def i64immSExt32 : PatLeaf<(i64 imm),
                [{return isInt<32>(N->getSExtValue()); }]>;
def i32immSExt32 : PatLeaf<(i32 imm),
                [{return isInt<32>(N->getSExtValue()); }]>;
def i64immZExt32 : PatLeaf<(i64 imm),
                [{return isUInt<32>(N->getZExtValue()); }]>;

def imm_to_i64 : SDNodeXForm<timm, [{
  return CurDAG->getTargetConstant(N->getZExtValue(), SDLoc(N), MVT::i64);
}]>;

// Fetch the upper 32-bits of a 64-bit integer.
def Upper32 : SDNodeXForm<imm, [{
  uint64_t value = N->getSExtValue() >> 32;
  return CurDAG->getTargetConstant(value, SDLoc(N),
                                   N->getValueType(0));
}]>;

// Fetch the lower 32-bits of a 64-bit integer.
def Lower32 : SDNodeXForm<imm, [{
  uint64_t value = N->getSExtValue() & 0x00000000ffffffff;
  return CurDAG->getTargetConstant(value, SDLoc(N),
                                   N->getValueType(0));
}]>;


// Addressing modes.
def ADDRri : ComplexPattern<i64, 2, "SelectAddr", [], []>;
def FIri : ComplexPattern<i64, 2, "SelectFIAddr", [add, or], []>;

// Address operands
def MEMri : Operand<i64> {
  let PrintMethod = "printMemOperand";
  let EncoderMethod = "getMemoryOpValue";
  let DecoderMethod = "decodeMemoryOpValue";
  let MIOperandInfo = (ops GPR, i16imm);
}

// Conditional code predicates - used for pattern matching for jump instructions
def SBF_CC_EQ  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETEQ);}]>;
def SBF_CC_NE  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETNE);}]>;
def SBF_CC_GE  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETGE);}]>;
def SBF_CC_GT  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETGT);}]>;
def SBF_CC_GTU : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETUGT);}]>;
def SBF_CC_GEU : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETUGE);}]>;
def SBF_CC_LE  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETLE);}]>;
def SBF_CC_LT  : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETLT);}]>;
def SBF_CC_LTU : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETULT);}]>;
def SBF_CC_LEU : PatLeaf<(i64 imm),
                         [{return (N->getZExtValue() == ISD::SETULE);}]>;

// For arithmetic and jump instructions the 8-bit 'code'
// field is divided into three parts:
//
//  +----------------+--------+--------------------+
//  |   4 bits       |  1 bit |   3 bits           |
//  | operation code | source | instruction class  |
//  +----------------+--------+--------------------+
//  (MSB)                                      (LSB)
class TYPE_ALU_JMP<bits<4> op, bits<1> srctype,
                   dag outs, dag ins, string asmstr, list<dag> pattern,
                   bit IsPqr64 = 0>
  : InstSBF<outs, ins, asmstr, pattern> {

  // In the PQR class, instructions that deal with 64-bit registers have a different OpCode.
  // To obtain it, we add one to its base value.
  let Inst{63-60} = !if(IsPqr64, !add(op, 1), op);
  let Inst{59} = srctype;
}

//For load and store instructions the 8-bit 'code' field is divided as:
//
//  +--------+--------+-------------------+
//  | 3 bits | 2 bits |   3 bits          |
//  |  mode  |  size  | instruction class |
//  +--------+--------+-------------------+
//  (MSB)                             (LSB)
class TYPE_LD_ST<bits<3> mode, bits<2> size,
                 dag outs, dag ins, string asmstr, list<dag> pattern>
  : InstSBF<outs, ins, asmstr, pattern> {

  let Inst{63-61} = mode;
  let Inst{60-59} = size;
}

//For load and store instructions in SBFv2 the 8-bit 'code' field is divided as:
//
//  +--------+---------------+-------------------+
//  | 4 bits | 1 bit         |   3 bits          |
//  |  size  |  source type  | instruction class |
//  +--------+---------------+-------------------+
//  (MSB)                             (LSB)
class TYPE_LD_ST_V2<bits<4> size, bits<1> srctype,
                 dag outs, dag ins, string asmstr, list<dag> pattern>
  : InstSBF<outs, ins, asmstr, pattern> {

  let Inst{63-60} = size;
  let Inst{59} = srctype;
}


// jump instructions
class JMP_RR<SBFJumpOp Opc, string Mnemonic, PatLeaf Cond>
    : TYPE_ALU_JMP<Opc.Value, SBF_X.Value,
                   (outs),
                   (ins GPR:$dst, GPR:$src, brtarget:$BrDst),
                   Mnemonic # " $dst, $src, $BrDst",
                   [(SBFbrcc i64:$dst, i64:$src, Cond, bb:$BrDst)]> {
  bits<4> dst;
  bits<4> src;
  bits<16> BrDst;

  let Inst{55-52} = src;
  let Inst{51-48} = dst;
  let Inst{47-32} = BrDst;
  let SBFClass = SBF_JMP;
}

class JMP_RI<SBFJumpOp Opc, string Mnemonic, PatLeaf Cond>
    : TYPE_ALU_JMP<Opc.Value, SBF_K.Value,
                   (outs),
                   (ins GPR:$dst, i64imm:$imm, brtarget:$BrDst),
                   Mnemonic # " $dst, $imm, $BrDst",
                   [(SBFbrcc i64:$dst, i64immSExt32:$imm, Cond, bb:$BrDst)]> {
  bits<4> dst;
  bits<16> BrDst;
  bits<32> imm;

  let Inst{51-48} = dst;
  let Inst{47-32} = BrDst;
  let Inst{31-0} = imm;
  let SBFClass = SBF_JMP;
}

multiclass J<SBFJumpOp Opc, string Mnemonic, PatLeaf Cond> {
  def _rr : JMP_RR<Opc, Mnemonic, Cond>;
  def _ri : JMP_RI<Opc, Mnemonic, Cond>;
}

let isBranch = 1, isTerminator = 1, hasDelaySlot=0 in {
// cmp+goto instructions
defm JEQ  : J<SBF_JEQ, "jeq", SBF_CC_EQ>;
defm JUGT : J<SBF_JGT, "jgt", SBF_CC_GTU>;
defm JUGE : J<SBF_JGE, "jge", SBF_CC_GEU>;
defm JNE  : J<SBF_JNE, "jne", SBF_CC_NE>;
defm JSGT : J<SBF_JSGT, "jsgt", SBF_CC_GT>;
defm JSGE : J<SBF_JSGE, "jsge", SBF_CC_GE>;
defm JULT : J<SBF_JLT, "jlt", SBF_CC_LTU>;
defm JULE : J<SBF_JLE, "jle", SBF_CC_LEU>;
defm JSLT : J<SBF_JSLT, "jslt", SBF_CC_LT>;
defm JSLE : J<SBF_JSLE, "jsle", SBF_CC_LE>;
}

// ALU instructions
class MATH_RI<SBFOpClass Class, SBFArithOp Opc,
             dag outs, dag ins, string asmstr,
             list<dag> pattern, bit isPqr64 = 0>
    : TYPE_ALU_JMP<Opc.Value, SBF_K.Value, outs, ins,
                           asmstr, pattern, isPqr64> {
  bits<4> dst;
  bits<32> imm;

  let Inst{51-48} = dst;
  let Inst{31-0} = imm;
  let SBFClass = Class;
}

class MATH_RR<SBFOpClass Class, SBFArithOp Opc,
               dag outs, dag ins, string asmstr,
                list<dag> pattern, bit isPqr64 = 0>
    : TYPE_ALU_JMP<Opc.Value, SBF_X.Value, outs, ins,
                           asmstr, pattern, isPqr64> {
  bits<4> dst;
  bits<4> src;

  let Inst{55-52} = src;
  let Inst{51-48} = dst;
  let SBFClass = Class;
}

multiclass MATH_32<SBFArithOp Opc, string Mnemonic,
                    SBFOpClass Class, SDNode OpNode, bit UseImmPat = 1> {
  def _rr_32 : MATH_RR<Class, Opc,
                   (outs GPR32:$dst),
                   (ins GPR32:$src2, GPR32:$src),
                   Mnemonic # "32 $dst, $src",
                   [(set GPR32:$dst, (OpNode i32:$src2, i32:$src))]>;
  def _ri_32 : MATH_RI<Class, Opc,
                   (outs GPR32:$dst),
                   (ins GPR32:$src2, i32imm:$imm),
                   Mnemonic # "32 $dst, $imm",
                   !if(UseImmPat,
                       [(set GPR32:$dst,
                             (OpNode GPR32:$src2, i32immSExt32:$imm))], [])>;
}

multiclass MATH_64<SBFArithOp Opc, string Mnemonic,
                     SBFOpClass Class, SDNode OpNode, bit UseImmPat = 1> {

  defvar isPqr64 = !if(!eq(Class, SBF_PQR), 1, 0);

  def _rr : MATH_RR<Class, Opc,
                   (outs GPR:$dst),
                   (ins GPR:$src2, GPR:$src),
                   Mnemonic # "64 $dst, $src",
                   [(set GPR:$dst, (OpNode i64:$src2, i64:$src))],
                   isPqr64>;

  def _ri : MATH_RI<Class, Opc,
                   (outs GPR:$dst),
                   (ins GPR:$src2, i64imm:$imm),
                   Mnemonic # "64 $dst, $imm",
                   !if(UseImmPat,
                       [(set GPR:$dst,
                            (OpNode GPR:$src2, i64immSExt32:$imm))], []),
                   isPqr64>;
}

multiclass ALU<SBFArithOp Opc, string Mnemonic,
                    SDNode OpNode, bit UseImmPat = 1> {
  defm "" : MATH_64<Opc, Mnemonic, SBF_ALU64, OpNode, UseImmPat>;

  defm "" : MATH_32<Opc, Mnemonic, SBF_ALU, OpNode, UseImmPat>;
}

multiclass PQR<SBFArithOp Opc, string Mnemonic, SDNode OpNode> {
  defm "" : MATH_64<Opc, Mnemonic, SBF_PQR, OpNode>;
  defm "" : MATH_32<Opc, Mnemonic, SBF_PQR, OpNode>;
}

let Constraints = "$dst = $src2" in {
    let isAsCheapAsAMove = 1 in {
        defm ADD : ALU<SBF_ADD, "add", add>;
        defm SUB : ALU<SBF_SUB, "sub", sub, 0>;
        defm OR  : ALU<SBF_OR, "or", or>;
        defm AND : ALU<SBF_AND, "and", and>;
        defm SLL : ALU<SBF_LSH, "lsh", shl>;
        defm SRL : ALU<SBF_RSH, "rsh", srl>;
        defm XOR : ALU<SBF_XOR, "xor", xor>;
        defm SRA : ALU<SBF_ARSH, "arsh", sra>;

        let Predicates = [SBFNoLddw] in {
            def HOR :  MATH_RI<SBF_ALU64, SBF_HOR,
                        (outs GPR:$dst),
                        (ins GPR:$src2, i32imm:$imm),
                        "hor64 $dst, $imm",
                        []>;
            let DecoderNamespace = "SBFv2" in {
              def HOR_addr :  MATH_RI<SBF_ALU64, SBF_HOR,
                                      (outs GPR:$dst),
                                      (ins GPR:$src2, u64imm:$imm),
                                      "hor64 $dst, $imm",
                                      []>;

            }
        }
    }


    let Predicates = [SBFNoPqrInstr] in {
        defm MUL : ALU<SBF_MUL, "mul", mul>;
        defm DIV : ALU<SBF_DIV, "div", udiv>;
        defm MOD : ALU<SBF_MOD, "mod", urem>;
    }

    let Predicates = [SBFPqrInstr] in {
        defm UHMUL    : MATH_64<PQR_UHMUL, "uhmul", SBF_PQR, mulhu>;
        defm UDIV     : PQR<PQR_UDIV, "udiv", udiv>;
        defm UREM     : PQR<PQR_UREM, "urem", urem>;
        defm LMUL     : PQR<PQR_LMUL, "lmul", mul>;
        defm SHMUL    : MATH_64<PQR_SHMUL, "shmul", SBF_PQR, mulhs>;
        defm SDIV_pqr : PQR<PQR_SDIV, "sdiv", sdiv>;
        defm SREM     : PQR<PQR_SREM, "srem", srem>;
    }
}

// Special case for SBFv2
// In SBFv1, `sub reg, imm` is interpreted as reg = reg - imm,
// but in SBFv2 it means reg = imm - reg
def : Pat<(sub GPR:$src, i64immSExt32:$imm),
          (SUB_ri GPR:$src, i64immSExt32:$imm)>, Requires<[SBFNoRevSub]>;
def : Pat<(sub GPR32:$src, i32immSExt32:$imm),
          (SUB_ri_32 GPR32:$src, i32immSExt32:$imm)>, Requires<[SBFNoRevSub]>;

def : Pat<(sub i64immSExt32:$imm, GPR:$src),
          (SUB_ri GPR:$src, i64immSExt32:$imm)>, Requires<[SBFRevSub]>;
def : Pat<(sub i32immSExt32:$imm, GPR32:$src),
          (SUB_ri_32 GPR32:$src, i32immSExt32:$imm)>, Requires<[SBFRevSub]>;

class NEG_RR<SBFOpClass Class, SBFArithOp Opc,
             dag outs, dag ins, string asmstr, list<dag> pattern>
    : TYPE_ALU_JMP<Opc.Value, 0, outs, ins, asmstr, pattern> {
  bits<4> dst;

  let Inst{51-48} = dst;
  let SBFClass = Class;
}

let Constraints = "$dst = $src", isAsCheapAsAMove = 1 in {
  def NEG_64: NEG_RR<SBF_ALU64, SBF_NEG, (outs GPR:$dst), (ins GPR:$src),
                     "neg64 $dst",
                     []>;
  def NEG_32: NEG_RR<SBF_ALU, SBF_NEG, (outs GPR32:$dst), (ins GPR32:$src),
                     "neg32 $dst",
                     []>;
}

// Instruction `neg` exists on SBFv1, but not on SBFv2
// In SBFv2, the negate operation is done with a subtraction
def : Pat<(ineg i64:$src), (NEG_64 GPR:$src)>, Requires<[SBFHasNeg]>;
def : Pat<(ineg i32:$src), (NEG_32 GPR32:$src)>, Requires<[SBFHasNeg]>;

def : Pat<(ineg i64:$src), (SUB_ri GPR:$src, 0)>, Requires<[SBFNoNeg]>;
def : Pat<(ineg i32:$src), (SUB_ri_32 GPR32:$src, 0)>, Requires<[SBFNoNeg]>;


class LD_IMM64<bits<4> Pseudo, string Mnemonic>
    : TYPE_LD_ST<SBF_IMM.Value, SBF_DW.Value,
                 (outs GPR:$dst),
                 (ins u64imm:$imm),
                 Mnemonic # " $dst, $imm",
                 [(set GPR:$dst, (i64 imm:$imm))]> {

  bits<4> dst;
  bits<64> imm;

  let Inst{51-48} = dst;
  let Inst{55-52} = Pseudo;
  let Inst{47-32} = 0;
  let Inst{31-0} = imm{31-0};
  let SBFClass = SBF_LD;
}

let isReMaterializable = 1, isAsCheapAsAMove = 1 in {
def LD_imm64 : LD_IMM64<0, "lddw">, Requires<[SBFHasLddw]>;
def MOV_rr : MATH_RR<SBF_ALU64, SBF_MOV,
                    (outs GPR:$dst),
                    (ins GPR:$src),
                    "mov64 $dst, $src",
                    []>;
def MOV_ri : MATH_RI<SBF_ALU64, SBF_MOV,
                    (outs GPR:$dst),
                    (ins i64imm:$imm),
                    "mov64 $dst, $imm",
                    [(set GPR:$dst, (i64 i64immSExt32:$imm))]>;

def MOV_ri_32 : MATH_RI<SBF_ALU, SBF_MOV,
                    (outs GPR32:$dst),
                    (ins i32imm:$imm),
                    "mov32 $dst, $imm",
                    [(set GPR32:$dst, (i32 i32immSExt32:$imm))]>;

let Predicates = [SBFExplicitSignExt], DecoderNamespace = "SBFv2" in {
    def MOV_rr_32_no_sext_v2 : MATH_RR<SBF_ALU64, SBF_MOV,
                                (outs GPR32:$dst),
                                (ins GPR32:$src),
                                "mov64 $dst, $src",
                                []>;
}

def MOV_rr_32_no_sext_v1 : MATH_RR<SBF_ALU, SBF_MOV,
                        (outs GPR32:$dst),
                        (ins GPR32:$src),
                        "mov32 $dst, $src",
                        []>, Requires<[SBFNoExplicitSignExt]>;
}

def FI_ri
    : TYPE_LD_ST<SBF_IMM.Value, SBF_DW.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr),
                 "lea\t$dst, $addr",
                 [(set i64:$dst, FIri:$addr)]> {
  // This is a tentative instruction, and will be replaced
  // with MOV_rr and ADD_ri in PEI phase
  let Inst{51-48} = 0;
  let Inst{55-52} = 2;
  let Inst{47-32} = 0;
  let Inst{31-0} = 0;
  let SBFClass = SBF_LD;
  bit isPseudo = true;
}

def LD_pseudo
    : TYPE_LD_ST<SBF_IMM.Value, SBF_DW.Value,
                 (outs GPR:$dst),
                 (ins i64imm:$pseudo, u64imm:$imm),
                 "ld_pseudo\t$dst, $pseudo, $imm",
                 [(set GPR:$dst, (int_bpf_pseudo imm:$pseudo, imm:$imm))]> {

  bits<4> dst;
  bits<64> imm;
  bits<4> pseudo;

  let Inst{51-48} = dst;
  let Inst{55-52} = pseudo;
  let Inst{47-32} = 0;
  let Inst{31-0} = imm{31-0};
  let SBFClass = SBF_LD;
}

// STORE instructions
class STORE_V1<SBFWidthModifer SizeOp, string Mnemonic>
    : TYPE_LD_ST<SBF_MEM.Value, SizeOp.Value,
                 (outs),
                 (ins GPR:$src, MEMri:$addr),
                 Mnemonic # " [$addr], $src",
                 []> {
  bits<4> src;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = src;
  let Inst{47-32} = addr{15-0}; // offset
  let SBFClass = SBF_STX;
}

class STORE_V2<SBFSizeModifier SizeOp, string Mnemonic>
    : TYPE_LD_ST_V2<SizeOp.Value, SBF_X.Value,
                 (outs),
                 (ins GPR:$src, MEMri:$addr),
                 Mnemonic # " [$addr], $src",
                 []> {
  bits<4> src;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = src;
  let Inst{47-32} = addr{15-0}; // offset
  let SBFClass = SBF_ST_V2;
}

multiclass STOREi64<SBFWidthModifer SizeV1, SBFSizeModifier SizeV2,
                                    string Mnemonic> {
    def _V1 : STORE_V1<SizeV1, Mnemonic>, Requires<[SBFOldMemEncoding]>;

    let DecoderNamespace = "SBFv2" in {
        def _V2 : STORE_V2<SizeV2, Mnemonic>, Requires<[SBFNewMemEncoding]>;
    }
}


defm STW : STOREi64<SBF_W, SBF_W_V2, "stxw">;
defm STH : STOREi64<SBF_H, SBF_H_V2, "stxh">;
defm STB : STOREi64<SBF_B, SBF_B_V2, "stxb">;
defm STD : STOREi64<SBF_DW, SBF_DW_V2, "stxdw">;

def : Pat<(store GPR:$src, ADDRri:$addr),
                 (STD_V1 GPR:$src, ADDRri:$addr)>, Requires<[SBFOldMemEncoding]>;

def : Pat<(store GPR:$src, ADDRri:$addr),
                 (STD_V2 GPR:$src, ADDRri:$addr)>, Requires<[SBFNewMemEncoding]>;

let Predicates = [SBFNoALU32, SBFOldMemEncoding] in {
    def : Pat<(truncstorei32 GPR:$src, ADDRri:$addr),
                (STW_V1 GPR:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei16 GPR:$src, ADDRri:$addr),
                (STH_V1 GPR:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei8 GPR:$src, ADDRri:$addr),
                (STB_V1 GPR:$src, ADDRri:$addr)>;
}

let Predicates = [SBFNoALU32, SBFNewMemEncoding] in {
    def : Pat<(truncstorei32 GPR:$src, ADDRri:$addr),
                (STW_V2 GPR:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei16 GPR:$src, ADDRri:$addr),
                (STH_V2 GPR:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei8 GPR:$src, ADDRri:$addr),
                (STB_V2 GPR:$src, ADDRri:$addr)>;
}


class STORE_imm_V1<SBFWidthModifer SizeOp,
                string Mnemonic>
    : TYPE_LD_ST<SBF_MEM.Value, SizeOp.Value,
                 (outs),
                 (ins i64imm:$imm, MEMri:$addr),
                 Mnemonic # " [$addr], $imm",
                 []> {
  bits<20> addr;
  bits<32> imm;
  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{47-32} = addr{15-0};  // offset
  let Inst{31-0} = imm;
  let SBFClass = SBF_ST;
}

class STORE_imm_V2<SBFSizeModifier SizeOp,
                string Mnemonic>
    : TYPE_LD_ST_V2<SizeOp.Value, SBF_K.Value,
                 (outs),
                 (ins i64imm:$imm, MEMri:$addr),
                 Mnemonic # " [$addr], $imm",
                 []> {
  bits<20> addr;
  bits<32> imm;
  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{47-32} = addr{15-0};  // offset
  let Inst{31-0} = imm;
  let SBFClass = SBF_ST_V2;
}

multiclass STORE_imm<SBFWidthModifer SizeV1, SBFSizeModifier SizeV2,
                    string Mnemonic> {
    def _V1 : STORE_imm_V1<SizeV1, Mnemonic>, Requires<[SBFOldMemEncoding]>;

    let DecoderNamespace = "SBFv2" in {
      def _V2 : STORE_imm_V2<SizeV2, Mnemonic>, Requires<[SBFNewMemEncoding]>;
    }
}

// Opcode (SBF_ST | SBF_MEM | SBF_DW) implies sign extension for
// value stored to memory:
// - it is fine to generate such write when immediate is -1
// - it is incorrect to generate such write when immediate is
//   +0xffff_ffff.
//
// In the latter case two instructions would be generated instead of
// one BPF_ST:
//   lddw rA, 0xffffffff
//   stx [rb], rA
//
// For SBF_{B,H,W} the size of value stored matches size of the immediate.
defm STD_imm : STORE_imm<SBF_DW, SBF_DW_V2, "stdw">;
defm STW_imm : STORE_imm<SBF_W, SBF_W_V2,  "stw">;
defm STH_imm : STORE_imm<SBF_H, SBF_H_V2, "sth">;
defm STB_imm : STORE_imm<SBF_B, SBF_B_V2,  "stb">;

let Predicates = [SBFHasStoreImm, SBFOldMemEncoding] in {
  def : Pat<(store (i64 i64immSExt32:$imm), ADDRri:$addr),
            (STD_imm_V1 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei32 (i64 i64immZExt32:$imm), ADDRri:$addr),
            (STW_imm_V1 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei16 (i64 i64immZExt32:$imm), ADDRri:$addr),
            (STH_imm_V1 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei8  (i64 i64immZExt32:$imm), ADDRri:$addr),
              (STB_imm_V1 (i64 imm:$imm), ADDRri:$addr)>;
}

let Predicates = [SBFHasStoreImm, SBFNewMemEncoding] in {
  def : Pat<(store (i64 i64immSExt32:$imm), ADDRri:$addr),
            (STD_imm_V2 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei32 (i64 i64immZExt32:$imm), ADDRri:$addr),
            (STW_imm_V2 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei16 (i64 i64immZExt32:$imm), ADDRri:$addr),
            (STH_imm_V2 (i64 imm:$imm), ADDRri:$addr)>;
  def : Pat<(truncstorei8  (i64 i64immZExt32:$imm), ADDRri:$addr),
              (STB_imm_V2 (i64 imm:$imm), ADDRri:$addr)>;
}

let Predicates = [SBFHasStoreImm, SBFNewMemEncoding] in {
  def : Pat<(store (i32 imm:$src), ADDRri:$dst),
            (STW_imm_V2 (imm_to_i64 $src), ADDRri:$dst)>;
  def : Pat<(truncstorei16 (i32 imm:$src), ADDRri:$dst),
            (STH_imm_V2 (imm_to_i64 imm:$src), ADDRri:$dst)>;
  def : Pat<(truncstorei8 (i32 imm:$src), ADDRri:$dst),
            (STB_imm_V2 (imm_to_i64 imm:$src), ADDRri:$dst)>;
}


let Predicates = [SBFHasALU32, SBFHasStoreImm, SBFOldMemEncoding] in {
  def : Pat<(store (i32 imm:$src), ADDRri:$dst),
            (STW_imm_V1 (imm_to_i64 $src), ADDRri:$dst)>;
  def : Pat<(truncstorei16 (i32 imm:$src), ADDRri:$dst),
            (STH_imm_V1 (imm_to_i64 imm:$src), ADDRri:$dst)>;
  def : Pat<(truncstorei8 (i32 imm:$src), ADDRri:$dst),
            (STB_imm_V1 (imm_to_i64 imm:$src), ADDRri:$dst)>;
}

let Predicates = [SBFHasALU32, SBFHasStoreImm, SBFNewMemEncoding] in {
  def : Pat<(store (i32 imm:$src), ADDRri:$dst),
            (STW_imm_V2 (imm_to_i64 $src), ADDRri:$dst)>;
  def : Pat<(truncstorei16 (i32 imm:$src), ADDRri:$dst),
            (STH_imm_V2 (imm_to_i64 imm:$src), ADDRri:$dst)>;
  def : Pat<(truncstorei8 (i32 imm:$src), ADDRri:$dst),
            (STB_imm_V2 (imm_to_i64 imm:$src), ADDRri:$dst)>;
}

// LOAD instructions
class LOAD_V1<SBFWidthModifer SizeOp, string Mnemonic>
    : TYPE_LD_ST<SBF_MEM.Value, SizeOp.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr),
                 Mnemonic # " $dst, [$addr]",
                 []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = dst;
  let Inst{55-52} = addr{19-16};
  let Inst{47-32} = addr{15-0};
  let SBFClass = SBF_LDX;
}

class LOAD_V2<SBFSizeModifier SizeOp, string Mnemonic>
    : TYPE_LD_ST_V2<SizeOp.Value, SBF_X.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr),
                 Mnemonic # " $dst, [$addr]",
                 []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = dst;
  let Inst{55-52} = addr{19-16};
  let Inst{47-32} = addr{15-0};
  let SBFClass = SBF_LD_V2;
}

multiclass LOADi64<SBFWidthModifer SizeV1, SBFSizeModifier SizeV2, string Mnemonic> {
  def _V1 : LOAD_V1<SizeV1, Mnemonic>, Requires<[SBFOldMemEncoding]>;

  let DecoderNamespace = "SBFv2" in {
     def _V2 : LOAD_V2<SizeV2, Mnemonic>, Requires<[SBFNewMemEncoding]>;
  }
}

let isCodeGenOnly = 1 in {
  multiclass CORE_LD<RegisterClass RegClass, string Sz> {
     def _V1 : TYPE_LD_ST<SBF_MEM.Value, SBF_W.Value,
                                       (outs RegClass:$dst),
                                       (ins u64imm:$opcode, GPR:$src, u64imm:$offset),
                                       "$dst = core_ld"#Sz#"($opcode, $src, $offset)",
                                       []>;

     def _V2 : TYPE_LD_ST_V2<SBF_W_V2.Value, SBF_X.Value,
                                    (outs RegClass:$dst),
                                    (ins u64imm:$opcode, GPR:$src, u64imm:$offset),
                                    "$dst = core_ld"#Sz#"($opcode, $src, $offset)",
                                       []>;
  }

  defm CORE_LD64 : CORE_LD<GPR, "64">;
  defm CORE_LD32 : CORE_LD<GPR32, "32">;

  def CORE_ST_V1   : TYPE_LD_ST<SBF_MEM.Value, SBF_W.Value,
                             (outs),
                             (ins gpr_or_imm:$src, u64imm:$opcode, GPR:$ptr, u64imm:$offset),
                             "core_st($src, $opcode, $ptr, $offset)",
                             []>;

  def CORE_ST_V2   : TYPE_LD_ST_V2<SBF_W_V2.Value, SBF_X.Value,
                             (outs),
                             (ins gpr_or_imm:$src, u64imm:$opcode, GPR:$ptr, u64imm:$offset),
                             "core_st($src, $opcode, $ptr, $offset)",
                             []>;

  let Constraints = "$dst = $src" in {
    def CORE_SHIFT : MATH_RR<SBF_ALU64, SBF_LSH,
                             (outs GPR:$dst),
                             (ins u64imm:$opcode, GPR:$src, u64imm:$offset),
                             "$dst = core_shift($opcode, $src, $offset)",
                             []>;
  }
}

defm LDW : LOADi64<SBF_W, SBF_W_V2, "ldxw">;
defm LDH : LOADi64<SBF_H, SBF_H_V2, "ldxh">;
defm LDB : LOADi64<SBF_B, SBF_B_V2, "ldxb">;
defm LDD : LOADi64<SBF_DW, SBF_DW_V2, "ldxdw">;

def : Pat<(load ADDRri:$addr),
                 (LDD_V1 ADDRri:$addr)>, Requires<[SBFOldMemEncoding]>;

def : Pat<(load ADDRri:$addr),
                 (LDD_V2 ADDRri:$addr)>, Requires<[SBFNewMemEncoding]>;

let Predicates = [SBFNoALU32, SBFOldMemEncoding] in {
    def : Pat<(zextloadi32 ADDRri:$addr),
                (LDW_V1 ADDRri:$addr)>;
    def : Pat<(zextloadi16 ADDRri:$addr),
                (LDH_V1 ADDRri:$addr)>;
    def : Pat<(zextloadi8 ADDRri:$addr),
                (LDB_V1 ADDRri:$addr)>;
}

let Predicates = [SBFNoALU32, SBFNewMemEncoding] in {
    def : Pat<(zextloadi32 ADDRri:$addr),
                (LDW_V2 ADDRri:$addr)>;
    def : Pat<(zextloadi16 ADDRri:$addr),
                (LDH_V2 ADDRri:$addr)>;
    def : Pat<(zextloadi8 ADDRri:$addr),
                (LDB_V2 ADDRri:$addr)>;
}

class BRANCH<SBFJumpOp Opc, string Mnemonic, list<dag> Pattern>
    : TYPE_ALU_JMP<Opc.Value, SBF_K.Value,
                   (outs),
                   (ins brtarget:$BrDst),
                   Mnemonic # " $BrDst",
                   Pattern> {
  bits<16> BrDst;

  let Inst{47-32} = BrDst;
  let SBFClass = SBF_JMP;
}

class CALL<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_CALL.Value, SBF_K.Value,
                   (outs),
                   (ins calltarget:$BrDst),
                   !strconcat(OpcodeStr, " $BrDst"),
                   []> {
  bits<32> BrDst;

  let Inst{31-0} = BrDst;
  let SBFClass = SBF_JMP;
}

class SYSCALL<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_SYSCALL.Value, SBF_K.Value,
                   (outs),
                   (ins i64imm:$imm),
                   !strconcat(OpcodeStr, " $imm"),
                   []> {
  bits<32> imm;

  let Inst{31-0} = imm;
  let SBFClass = SBF_JMP;
}


class CALLX<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_CALL.Value, SBF_X.Value,
                   (outs),
                   (ins GPR:$BrDst),
                   !strconcat(OpcodeStr, " $BrDst"),
                   []> {
  bits<32> BrDst;

  let Inst{31-0} = BrDst;
  let SBFClass = SBF_JMP;
}

class CALLX_SRC_REG<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_CALL.Value, SBF_X.Value,
                   (outs),
                   (ins GPR:$BrDst),
                   !strconcat(OpcodeStr, " $BrDst"),
                   []> {
  bits<4> BrDst;

  let Inst{55-52} = BrDst;
  let SBFClass = SBF_JMP;
}

// Jump always
let isBranch = 1, isTerminator = 1, hasDelaySlot=0, isBarrier = 1 in {
  def JMP : BRANCH<SBF_JA, "ja", [(br bb:$BrDst)]>;
}

// Jump and link
let isCall=1, hasDelaySlot=0, Uses = [R10],
    // Potentially clobbered registers
    Defs = [R0, R1, R2, R3, R4, R5] in {
  def JAL     : CALL<"call">;
  def JALX    : CALLX<"callx">, Requires<[SBFNoCallxSrc]>;
  let DecoderNamespace = "SBFv2" in {
    def JALX_v2 : CALLX_SRC_REG<"callx">, Requires<[SBFCallxSrc]>;
    def SYSCALL_v3 : SYSCALL<"syscall">, Requires<[SBFHasStaticSyscalls]>;
  }
}

class NOP_I<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_MOV.Value, SBF_X.Value,
                   (outs),
                   (ins i32imm:$imm),
                   !strconcat(OpcodeStr, "\t$imm"),
                   []> {
  // mov r0, r0 == nop
  let Inst{55-52} = 0;
  let Inst{51-48} = 0;
  let SBFClass = SBF_ALU64;
}

let hasSideEffects = 0, isCodeGenOnly = 1 in
  def NOP : NOP_I<"nop">;

class EXIT<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_EXIT.Value, SBF_K.Value,
                   (outs),
                   (ins),
                   !strconcat(OpcodeStr, ""),
                   [(SBFretglue)]> {
  let Inst{31-0} = 0;
  let SBFClass = SBF_JMP;
}

let isReturn = 1, isTerminator = 1, hasDelaySlot=0, isBarrier = 1,
    isNotDuplicable = 1, Predicates = [SBFNoStaticSyscalls] in {
  def EXIT : EXIT<"exit">;
}

class RETURN<string OpcodeStr>
    : TYPE_ALU_JMP<SBF_EXIT.Value, SBF_X.Value,
                   (outs),
                   (ins),
                   !strconcat(OpcodeStr, ""),
                   [(SBFretglue)]> {
  let Inst{31-0} = 0;
  let SBFClass = SBF_JMP;
}

let isReturn = 1, isTerminator = 1, hasDelaySlot=0, isBarrier = 1,
    isNotDuplicable = 1, Predicates = [SBFHasStaticSyscalls] in {
  def RETURN_v3 : RETURN<"return">;
}

// ADJCALLSTACKDOWN/UP pseudo insns
let Defs = [R10], Uses = [R10], isCodeGenOnly = 1 in {
def ADJCALLSTACKDOWN : Pseudo<(outs), (ins i64imm:$amt1, i64imm:$amt2),
                              "#ADJCALLSTACKDOWN $amt1 $amt2",
                              [(SBFcallseq_start timm:$amt1, timm:$amt2)]>;
def ADJCALLSTACKUP   : Pseudo<(outs), (ins i64imm:$amt1, i64imm:$amt2),
                              "#ADJCALLSTACKUP $amt1 $amt2",
                              [(SBFcallseq_end timm:$amt1, timm:$amt2)]>;
}

let usesCustomInserter = 1, isCodeGenOnly = 1 in {
  def Select : Pseudo<(outs GPR:$dst),
                      (ins GPR:$lhs, GPR:$rhs, i64imm:$imm, GPR:$src, GPR:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i64:$dst,
                       (SBFselectcc i64:$lhs, i64:$rhs, (i64 imm:$imm), i64:$src, i64:$src2))]>;
  def Select_Ri : Pseudo<(outs GPR:$dst),
                      (ins GPR:$lhs, i64imm:$rhs, i64imm:$imm, GPR:$src, GPR:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i64:$dst,
                       (SBFselectcc i64:$lhs, (i64immSExt32:$rhs), (i64 imm:$imm), i64:$src, i64:$src2))]>;
  def Select_64_32 : Pseudo<(outs GPR32:$dst),
                      (ins GPR:$lhs, GPR:$rhs, i64imm:$imm, GPR32:$src, GPR32:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i32:$dst,
                       (SBFselectcc i64:$lhs, i64:$rhs, (i64 imm:$imm), i32:$src, i32:$src2))]>;
  def Select_Ri_64_32 : Pseudo<(outs GPR32:$dst),
                      (ins GPR:$lhs, i64imm:$rhs, i64imm:$imm, GPR32:$src, GPR32:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i32:$dst,
                       (SBFselectcc i64:$lhs, (i64immSExt32:$rhs), (i64 imm:$imm), i32:$src, i32:$src2))]>;
  def Select_32 : Pseudo<(outs GPR32:$dst),
                      (ins GPR32:$lhs, GPR32:$rhs, i32imm:$imm, GPR32:$src, GPR32:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i32:$dst,
                       (SBFselectcc i32:$lhs, i32:$rhs, (i32 imm:$imm), i32:$src, i32:$src2))]>;
  def Select_Ri_32 : Pseudo<(outs GPR32:$dst),
                      (ins GPR32:$lhs, i32imm:$rhs, i32imm:$imm, GPR32:$src, GPR32:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i32:$dst,
                       (SBFselectcc i32:$lhs, (i32immSExt32:$rhs), (i32 imm:$imm), i32:$src, i32:$src2))]>;
  def Select_32_64 : Pseudo<(outs GPR:$dst),
                      (ins GPR32:$lhs, GPR32:$rhs, i32imm:$imm, GPR:$src, GPR:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i64:$dst,
                       (SBFselectcc i32:$lhs, i32:$rhs, (i32 imm:$imm), i64:$src, i64:$src2))]>;
  def Select_Ri_32_64 : Pseudo<(outs GPR:$dst),
                      (ins GPR32:$lhs, i32imm:$rhs, i32imm:$imm, GPR:$src, GPR:$src2),
                      "# Select PSEUDO $dst = $lhs $imm $rhs ? $src : $src2",
                      [(set i64:$dst,
                       (SBFselectcc i32:$lhs, (i32immSExt32:$rhs), (i32 imm:$imm), i64:$src, i64:$src2))]>;
}

// 0xffffFFFF doesn't fit into simm32, optimize common case
def : Pat<(i64 (and (i64 GPR:$src), 0xffffFFFF)),
          (SRL_ri (SLL_ri (i64 GPR:$src), 32), 32)>;

// Calls
def : Pat<(SBFcall tglobaladdr:$dst), (JAL tglobaladdr:$dst)>;
def : Pat<(SBFcall texternalsym:$dst), (JAL texternalsym:$dst)>;
def : Pat<(SBFcall imm:$dst), (JAL imm:$dst)>, Requires<[SBFNoStaticSyscalls]>;
def : Pat<(SBFcall GPR:$dst), (JALX GPR:$dst)>, Requires<[SBFNoCallxSrc]>;
def : Pat<(SBFcall GPR:$dst), (JALX_v2 GPR:$dst)>, Requires<[SBFCallxSrc]>;
def : Pat<(SBFcall imm:$imm), (SYSCALL_v3 imm:$imm)>, Requires<[SBFHasStaticSyscalls]>;

// Loads
let Predicates = [SBFNoALU32, SBFOldMemEncoding] in {
  def : Pat<(i64 (extloadi8  ADDRri:$src)), (i64 (LDB_V1 ADDRri:$src))>;
  def : Pat<(i64 (extloadi16 ADDRri:$src)), (i64 (LDH_V1 ADDRri:$src))>;
  def : Pat<(i64 (extloadi32 ADDRri:$src)), (i64 (LDW_V1 ADDRri:$src))>;
}

let Predicates = [SBFNoALU32, SBFNewMemEncoding] in {
  def : Pat<(i64 (extloadi8  ADDRri:$src)), (i64 (LDB_V2 ADDRri:$src))>;
  def : Pat<(i64 (extloadi16 ADDRri:$src)), (i64 (LDH_V2 ADDRri:$src))>;
  def : Pat<(i64 (extloadi32 ADDRri:$src)), (i64 (LDW_V2 ADDRri:$src))>;
}

// Atomic XADD for SBFNoALU32
class XADD<SBFWidthModifer SizeOp, string Mnemonic, PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr, GPR:$val),
                 Mnemonic # " [$addr], $val",
                 [(set GPR:$dst, (OpNode ADDRri:$addr, GPR:$val))]> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = SBF_ADD.Value;
  let SBFClass = SBF_STX;
}

let Constraints = "$dst = $val" in {
  let Predicates = [SBFNoALU32] in {
    def XADDW : XADD<SBF_W, "stxxaddw", atomic_load_add_32>;
  }
}

// Atomic add, and, or, xor
class ATOMIC_NOFETCH<SBFArithOp Opc, string Mnemonic>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SBF_DW.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr, GPR:$val),
                 "stxx" # Mnemonic # "dw [$addr], $val",
                 []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = Opc.Value;
  let SBFClass = SBF_STX;
}

class ATOMIC32_NOFETCH<SBFArithOp Opc, string Mnemonic>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SBF_W.Value,
                 (outs GPR32:$dst),
                 (ins MEMri:$addr, GPR32:$val),
                 "stxx" # Mnemonic # "w [$addr], $val",
                 []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = Opc.Value;
  let SBFClass = SBF_STX;
}

let Constraints = "$dst = $val" in {
  let Predicates = [SBFHasALU32], DecoderNamespace = "SBFALU32" in {
    def XADDW32 : ATOMIC32_NOFETCH<SBF_ADD, "add">;
    def XANDW32 : ATOMIC32_NOFETCH<SBF_AND, "and">;
    def XORW32  : ATOMIC32_NOFETCH<SBF_OR, "or">;
    def XXORW32 : ATOMIC32_NOFETCH<SBF_XOR, "xor">;
  }

  def XADDD  : ATOMIC_NOFETCH<SBF_ADD, "add">;
  def XANDD  : ATOMIC_NOFETCH<SBF_AND, "and">;
  def XORD   : ATOMIC_NOFETCH<SBF_OR, "or">;
  def XXORD  : ATOMIC_NOFETCH<SBF_XOR,"xor">;
}

// Atomic Fetch-and-<add, and, or, xor> operations
class XFALU64<SBFWidthModifer SizeOp, SBFArithOp Opc, string OpcStr,
              PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr, GPR:$val),
                 "stxxf" # OpcStr # "dw [$addr], $val",
                 [(set GPR:$dst, (OpNode ADDRri:$addr, GPR:$val))]> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = Opc.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

class XFALU32<SBFWidthModifer SizeOp, SBFArithOp Opc, string OpcStr,
              PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs GPR32:$dst),
                 (ins MEMri:$addr, GPR32:$val),
                 "stxxf" # OpcStr  # "w [$addr], $val",
                 [(set GPR32:$dst, (OpNode ADDRri:$addr, GPR32:$val))]> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = Opc.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

let Constraints = "$dst = $val" in {
  let Predicates = [SBFHasALU32], DecoderNamespace = "SBFALU32" in {
    def XFADDW32 : XFALU32<SBF_W, SBF_ADD, "add", atomic_load_add_32>;
    def XFANDW32 : XFALU32<SBF_W, SBF_AND, "and", atomic_load_and_32>;
    def XFORW32  : XFALU32<SBF_W, SBF_OR,  "or",  atomic_load_or_32>;
    def XFXORW32 : XFALU32<SBF_W, SBF_XOR, "xor", atomic_load_xor_32>;
  }

  def XFADDD : XFALU64<SBF_DW, SBF_ADD, "add", atomic_load_add_64>;
  def XFANDD : XFALU64<SBF_DW, SBF_AND, "and", atomic_load_and_64>;
  def XFORD  : XFALU64<SBF_DW, SBF_OR,  "or",  atomic_load_or_64>;
  def XFXORD : XFALU64<SBF_DW, SBF_XOR, "xor", atomic_load_xor_64>;
}

let usesCustomInserter = 1, isCodeGenOnly = 1 in {
  def ATOMIC_FENCE : Pseudo<
    (outs),
    (ins),
    "#atomic_fence",
    [(atomic_fence timm, timm)]>;
}

// Atomic Exchange
class XCHG<SBFWidthModifer SizeOp, PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs GPR:$dst),
                 (ins MEMri:$addr, GPR:$val),
                 "stxxchgdw [$addr], $val",
                 [(set GPR:$dst, (OpNode ADDRri:$addr,GPR:$val))]> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = SBF_XCHG.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

class XCHG32<SBFWidthModifer SizeOp, PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs GPR32:$dst),
                 (ins MEMri:$addr, GPR32:$val),
                 "stxxchgw [$addr], $val",
                 [(set GPR32:$dst, (OpNode ADDRri:$addr,GPR32:$val))]> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = dst;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = SBF_XCHG.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

let Constraints = "$dst = $val" in {
  let Predicates = [SBFHasALU32], DecoderNamespace = "SBFALU32" in {
    def XCHGW32 : XCHG32<SBF_W, atomic_swap_32>;
  }

  def XCHGD : XCHG<SBF_DW, atomic_swap_64>;
}

// Compare-And-Exchange
class CMPXCHG<SBFWidthModifer SizeOp, PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs),
                 (ins MEMri:$addr, GPR:$new),
                 "stxcmpxchgdw [$addr], $new",
                 [(set R0, (OpNode ADDRri:$addr, R0, GPR:$new))]> {
  bits<4> new;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = new;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = SBF_CMPXCHG.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

class CMPXCHG32<SBFWidthModifer SizeOp, PatFrag OpNode>
    : TYPE_LD_ST<SBF_ATOMIC.Value, SizeOp.Value,
                 (outs),
                 (ins MEMri:$addr, GPR32:$new),
                 "stxcmpxchgw [$addr], $new",
                 [(set W0, (OpNode ADDRri:$addr, W0, GPR32:$new))]> {
  bits<4> new;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = new;
  let Inst{47-32} = addr{15-0}; // offset
  let Inst{7-4} = SBF_CMPXCHG.Value;
  let Inst{3-0} = SBF_FETCH.Value;
  let SBFClass = SBF_STX;
}

let Predicates = [SBFHasALU32], Defs = [W0], Uses = [W0],
    DecoderNamespace = "SBFALU32" in {
  def CMPXCHGW32 : CMPXCHG32<SBF_W, atomic_cmp_swap_32>;
}

let Defs = [R0], Uses = [R0] in {
  def CMPXCHGD : CMPXCHG<SBF_DW, atomic_cmp_swap_64>;
}

// bswap16, bswap32, bswap64
class BSWAP<bits<32> SizeOp, string OpcodeStr, SBFSrcType SrcType, list<dag> Pattern>
    : TYPE_ALU_JMP<SBF_END.Value, SrcType.Value,
                   (outs GPR:$dst),
                   (ins GPR:$src),
                   OpcodeStr # " $src",
                   Pattern> {
  bits<4> dst;

  let Inst{51-48} = dst;
  let Inst{31-0} = SizeOp;
  let SBFClass = SBF_ALU;
}


let Constraints = "$dst = $src" in {
    let Predicates = [SBFIsLittleEndian] in {
        def BE16 : BSWAP<16, "be16", SBF_TO_BE, [(set GPR:$dst, (srl (bswap GPR:$src), (i64 48)))]>;
        def BE32 : BSWAP<32, "be32", SBF_TO_BE, [(set GPR:$dst, (srl (bswap GPR:$src), (i64 32)))]>;
        def BE64 : BSWAP<64, "be64", SBF_TO_BE, [(set GPR:$dst, (bswap GPR:$src))]>;
    }
}

let DecoderNamespace = "SBFv2" in {
  def MOV_32_64 : MATH_RR<SBF_ALU, SBF_MOV,
                         (outs GPR:$dst), (ins GPR32:$src),
                         "mov32 $dst, $src", []>;
}

let isCodeGenOnly = 1 in {
  def MOV_32_64_addr : MATH_RI<SBF_ALU, SBF_MOV,
                           (outs GPR:$dst), (ins u64imm:$imm),
                           "mov32 $dst, $imm", []>, Requires<[SBFNoLddw]>;

  def MOV_32_64_no_sext : MATH_RR<SBF_ALU64, SBF_MOV,
                                    (outs GPR:$dst),
                                    (ins GPR32:$src),
                                    "mov64 $dst, $src",
                                    []>;
}

let DecoderNamespace = "SBFv2", Predicates = [SBFNoLddw] in {
  def MOV_32_64_imm : MATH_RI<SBF_ALU, SBF_MOV,
                               (outs GPR:$dst), (ins i32imm:$imm),
                               "mov32 $dst, $imm", []>;
}

// In SBFv2, a CopyToReg of a 64-bit value is split in two instructions:
// mov32 r1, 0x55667788
// hor r1, 0x11223344
// These instructions copy the value 0x1122334455667788 to a register.
def : Pat<(i64 imm:$imm),
            (HOR (MOV_32_64_imm (i32 (Lower32 $imm))),
                       (i32 (Upper32 $imm)))>, Requires<[SBFNoLddw]>;

// load 64-bit global address into register.
def : Pat<(SBFWrapper tglobaladdr:$in), (LD_imm64 tglobaladdr:$in)>,
                                                    Requires<[SBFHasLddw]>;
def : Pat<(SBFWrapper tglobaladdr:$in),
        (HOR_addr (MOV_32_64_addr tglobaladdr:$in),
                            tglobaladdr:$in)>, Requires<[SBFNoLddw]>;

// SBFv2 sign extension
def : Pat<(i64 (sext GPR32:$src)),
          (MOV_32_64 GPR32:$src)>, Requires<[SBFExplicitSignExt]>;

// SBFv1 sign extension
def : Pat<(i64 (sext GPR32:$src)),
          (SRA_ri (SLL_ri (MOV_32_64 GPR32:$src), 32), 32)>,
                Requires<[SBFNoExplicitSignExt]>;

// SBFv2 zero extension
def : Pat<(i64 (zext GPR32:$src)), (INSERT_SUBREG (i64 (IMPLICIT_DEF)),
                                    GPR32:$src, sub_32)>, Requires<[SBFExplicitSignExt]>;

// SBFv1 zero extension
def : Pat<(i64 (zext GPR32:$src)), (MOV_32_64 GPR32:$src)>,
                                Requires<[SBFNoExplicitSignExt]>;

// SBFv2 truncation
def : Pat<(i32 (trunc GPR:$src)),
          (AND_ri_32 (i32 (EXTRACT_SUBREG GPR:$src, sub_32)),
          (i32 0xffffffff))>, Requires<[SBFExplicitSignExt]>;

// SBFv1 truncation
def : Pat<(i32 (trunc GPR:$src)),
          (i32 (EXTRACT_SUBREG GPR:$src, sub_32))>, Requires<[SBFNoExplicitSignExt]>;

// SBFv2 anyext
def : Pat<(i64 (anyext GPR32:$src)),
          (MOV_32_64 GPR32:$src)>, Requires<[SBFExplicitSignExt]>;

// SBFv1 anyext
def : Pat<(i64 (anyext GPR32:$src)),
          (INSERT_SUBREG (i64 (IMPLICIT_DEF)), GPR32:$src, sub_32)>, Requires<[SBFNoExplicitSignExt]>;

class STORE32_V1<SBFWidthModifer SizeOp, string Mnemonic>
    : TYPE_LD_ST<SBF_MEM.Value, SizeOp.Value,
                 (outs),
                 (ins GPR32:$src, MEMri:$addr),
                 Mnemonic # " [$addr], $src",
                 []> {
  bits<4> src;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = src;
  let Inst{47-32} = addr{15-0}; // offset
  let SBFClass = SBF_STX;
}

class STORE32_V2<SBFSizeModifier SizeOp, string Mnemonic>
    : TYPE_LD_ST_V2<SizeOp.Value,
                 SBF_X.Value,
                 (outs),
                 (ins GPR32:$src, MEMri:$addr),
                 Mnemonic # " [$addr], $src",
                 []> {
  bits<4> src;
  bits<20> addr;

  let Inst{51-48} = addr{19-16}; // base reg
  let Inst{55-52} = src;
  let Inst{47-32} = addr{15-0}; // offset
  let SBFClass = SBF_ST_V2;
}

multiclass STOREi32<SBFWidthModifer SizeV1, SBFSizeModifier SizeV2,
                                    string Mnemonic> {
    let DecoderNamespace = "SBFALU32" in {
      def _V1 : STORE32_V1<SizeV1, Mnemonic>, Requires<[SBFOldMemEncoding]>;
    }

    let DecoderNamespace = "SBFALU32MEMv2" in {
      def _V2 : STORE32_V2<SizeV2, Mnemonic>, Requires<[SBFNewMemEncoding]>;
    }
}

defm STW32 : STOREi32<SBF_W, SBF_W_V2, "stxw">;
defm STH32 : STOREi32<SBF_H, SBF_H_V2, "stxh">;
defm STB32 : STOREi32<SBF_B, SBF_B_V2, "stxb">;

let Predicates = [SBFHasALU32, SBFOldMemEncoding] in {
    def : Pat<(store GPR32:$src, ADDRri:$addr),
                (STW32_V1 GPR32:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei16 GPR32:$src, ADDRri:$addr),
                (STH32_V1 GPR32:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei8 GPR32:$src, ADDRri:$addr),
                (STB32_V1 GPR32:$src, ADDRri:$addr)>;
}

let Predicates = [SBFHasALU32, SBFNewMemEncoding] in {
    def : Pat<(store GPR32:$src, ADDRri:$addr),
                (STW32_V2 GPR32:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei16 GPR32:$src, ADDRri:$addr),
                (STH32_V2 GPR32:$src, ADDRri:$addr)>;
    def : Pat<(truncstorei8 GPR32:$src, ADDRri:$addr),
                (STB32_V2 GPR32:$src, ADDRri:$addr)>;
}

class LOAD32_V1<SBFWidthModifer SizeOp, string Mnemonic>
    : TYPE_LD_ST<SBF_MEM.Value, SizeOp.Value,
                (outs GPR32:$dst),
                (ins MEMri:$addr),
                Mnemonic # " $dst, [$addr]",
                []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = dst;
  let Inst{55-52} = addr{19-16};
  let Inst{47-32} = addr{15-0};
  let SBFClass = SBF_LDX;
}

class LOAD32_V2<SBFSizeModifier SizeOp, string Mnemonic>
    : TYPE_LD_ST_V2<SizeOp.Value, SBF_X.Value,
                (outs GPR32:$dst),
                (ins MEMri:$addr),
                Mnemonic # " $dst, [$addr]",
                []> {
  bits<4> dst;
  bits<20> addr;

  let Inst{51-48} = dst;
  let Inst{55-52} = addr{19-16};
  let Inst{47-32} = addr{15-0};
  let SBFClass = SBF_LD_V2;
}


multiclass LOADi32<SBFWidthModifer SizeV1, SBFSizeModifier SizeV2,
                                    string Mnemonic> {
 let DecoderNamespace = "SBFALU32" in {
    def _V1 : LOAD32_V1<SizeV1, Mnemonic>, Requires<[SBFOldMemEncoding]>;
 }
 let DecoderNamespace = "SBFALU32MEMv2" in {
   def _V2 : LOAD32_V2<SizeV2, Mnemonic>, Requires<[SBFNewMemEncoding]>;
 }
}


defm LDW32 : LOADi32<SBF_W, SBF_W_V2, "ldxw">;
defm LDH32 : LOADi32<SBF_H, SBF_H_V2, "ldxh">;
defm LDB32 : LOADi32<SBF_B, SBF_B_V2, "ldxb">;

let Predicates = [SBFHasALU32, SBFOldMemEncoding] in {
    def : Pat<(load ADDRri:$addr),
                (LDW32_V1 ADDRri:$addr)>;
    def : Pat<(zextloadi16 ADDRri:$addr),
                (LDH32_V1 ADDRri:$addr)>;
    def : Pat<(zextloadi8 ADDRri:$addr),
                (LDB32_V1 ADDRri:$addr)>;
}

let Predicates = [SBFHasALU32, SBFNewMemEncoding] in {
    def : Pat<(load ADDRri:$addr),
                (LDW32_V2 ADDRri:$addr)>;
    def : Pat<(zextloadi16 ADDRri:$addr),
                (LDH32_V2 ADDRri:$addr)>;
    def : Pat<(zextloadi8 ADDRri:$addr),
                (LDB32_V2 ADDRri:$addr)>;
}

let Predicates = [SBFHasALU32, SBFOldMemEncoding] in {
  def : Pat<(truncstorei8 GPR:$src, ADDRri:$dst),
            (STB32_V1 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(truncstorei16 GPR:$src, ADDRri:$dst),
            (STH32_V1 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(truncstorei32 GPR:$src, ADDRri:$dst),
            (STW32_V1 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(i32 (extloadi8 ADDRri:$src)), (i32 (LDB32_V1 ADDRri:$src))>;
  def : Pat<(i32 (extloadi16 ADDRri:$src)), (i32 (LDH32_V1 ADDRri:$src))>;
  def : Pat<(i64 (zextloadi8  ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDB32_V1 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (zextloadi16 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDH32_V1 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (zextloadi32 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDW32_V1 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi8  ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDB32_V1 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi16 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDH32_V1 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi32 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDW32_V1 ADDRri:$src), sub_32)>;
}

let Predicates = [SBFHasALU32, SBFNewMemEncoding] in {
  def : Pat<(truncstorei8 GPR:$src, ADDRri:$dst),
            (STB32_V2 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(truncstorei16 GPR:$src, ADDRri:$dst),
            (STH32_V2 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(truncstorei32 GPR:$src, ADDRri:$dst),
            (STW32_V2 (EXTRACT_SUBREG GPR:$src, sub_32), ADDRri:$dst)>;
  def : Pat<(i32 (extloadi8 ADDRri:$src)), (i32 (LDB32_V2 ADDRri:$src))>;
  def : Pat<(i32 (extloadi16 ADDRri:$src)), (i32 (LDH32_V2 ADDRri:$src))>;
  def : Pat<(i64 (zextloadi8  ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDB32_V2 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (zextloadi16 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDH32_V2 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (zextloadi32 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDW32_V2 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi8  ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDB32_V2 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi16 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDH32_V2 ADDRri:$src), sub_32)>;
  def : Pat<(i64 (extloadi32 ADDRri:$src)),
            (SUBREG_TO_REG (i64 0), (LDW32_V2 ADDRri:$src), sub_32)>;
}
