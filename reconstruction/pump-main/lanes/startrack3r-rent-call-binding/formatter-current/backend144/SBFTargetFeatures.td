//===-- SBFTargetFeatures.td - Target Features for SBF Target ---------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file describes the SBF target features in TableGen format.
//
//===----------------------------------------------------------------------===//

def ALU32 : SubtargetFeature<"alu32", "HasAlu32", "true",
                             "Enable ALU32 instructions">;

def DwarfRIS: SubtargetFeature<"dwarfris", "UseDwarfRIS", "true",
                               "Disable MCAsmInfo DwarfUsesRelocationsAcrossSections">;

def FeatureDynamicFrames : SubtargetFeature<"dynamic-frames", "HasDynamicFrames", "true",
                                            "Enable dynamic frames">;

def FeatureRelocAbs64 : SubtargetFeature<"reloc-abs64", "UseRelocAbs64", "true",
                                   "Fix 64bit data relocations">;

def FeatureStaticSyscalls : SubtargetFeature<"static-syscalls", "HasStaticSyscalls", "true",
                                   "Enable static syscalls">;

def FeatureDisableNeg : SubtargetFeature<"no-neg", "DisableNeg", "true",
                                    "Disable the neg instruction">;

def FeatureReverseSubImm : SubtargetFeature<"reverse-sub", "ReverseSubImm", "true",
                                    "Reverse the operands in the 'sub reg, imm' instruction">;

def FeatureDisableLddw : SubtargetFeature<"no-lddw", "NoLddw", "true",
                                    "Disable the lddw instruction">;

def FeatureCallxRegSrc : SubtargetFeature<"callx-reg-src", "CallxRegSrc", "true",
                                    "Encode Callx destination register in the src field">;

def FeaturePqrInstr : SubtargetFeature<"pqr-instr", "HasPqrClass", "true",
                                    "Enable the PQR instruction class">;

def FeatureStoreImm : SubtargetFeature<"store-imm", "HasStoreImm", "true",
                                           "Enable store imm instructions">;

def FeatureExplicitSext : SubtargetFeature<"explicit-sext", "HasExplicitSignExt",
                    "true", "Enable the explicit sign extension instruction mov32">;

def FeatureNewMemEncoding : SubtargetFeature<"mem-encoding", "NewMemEncoding",
                                       "true", "Enable the new encoding for memory instructions">;

def FeatureJumpExt : SubtargetFeature<"jmp-ext", "HasJmpExt",
                                       "true", "Enable jumps with less than and less than or equal">;

class Proc<string Name, list<SubtargetFeature> Features>
 : Processor<Name, NoItineraries, Features>;

def : Proc<"generic", []>;

def : Proc<"v1", [FeatureDynamicFrames, FeatureStoreImm, FeatureJumpExt]>;
def : Proc<"v2", [FeatureDynamicFrames, FeatureStoreImm, FeatureJumpExt, FeatureDisableLddw,
                  FeatureNewMemEncoding, FeatureCallxRegSrc, FeaturePqrInstr, FeatureExplicitSext,
                  FeatureDisableNeg, FeatureReverseSubImm, ALU32]>;
def : Proc<"v3", [FeatureDynamicFrames, FeatureStoreImm, FeatureJumpExt, FeatureDisableLddw,
                  FeatureNewMemEncoding, FeatureCallxRegSrc, FeaturePqrInstr, FeatureExplicitSext,
                  FeatureDisableNeg, FeatureReverseSubImm, ALU32, FeatureStaticSyscalls, FeatureRelocAbs64]>;