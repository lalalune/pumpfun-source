//! Regression tests for the SBF window decoder.
//!
//! `lddw` (opcode 0x18) is a 16-byte paired instruction. A window ending on
//! the first slot must be refused instead of reading the high word past the
//! window (or panicking when the window ends with the file).

use super::*;

/// One complete lddw pair: low half in bytes 0..8, high word in 12..16.
fn lddw_pair(dst: u8, imm: u32, hi: u32) -> [u8; 16] {
    let mut bytes = [0u8; 16];
    bytes[0] = 0x18;
    bytes[1] = dst & 0x0F;
    bytes[4..8].copy_from_slice(&imm.to_le_bytes());
    bytes[12..16].copy_from_slice(&hi.to_le_bytes());
    bytes
}

#[test]
fn decode_decodes_a_complete_lddw_pair() {
    let bytes = lddw_pair(1, 0x1234_5678, 0xdead_beef);
    let insns = decode(&bytes, 0, 0x1000, 16).expect("complete pair decodes");
    assert_eq!(insns.len(), 1);
    assert_eq!(render(insns[0], &bytes, 0), "lddw r1, 0xdeadbeef12345678");
}

#[test]
fn decode_refuses_an_lddw_cut_at_end_of_file() {
    let pair = lddw_pair(1, 0x1234_5678, 0xdead_beef);
    let err = decode(&pair[..8], 0, 0x1000, 8).err().expect("a cut pair must be refused");
    assert!(err.contains("lddw"), "{err}");
    assert!(err.contains("0x1000"), "{err}");
}

#[test]
fn decode_refuses_an_lddw_cut_before_file_end() {
    let pair = lddw_pair(1, 0x1234_5678, 0xdead_beef);
    // The bytes past the window are readable, so before the fix this decoded
    // with the out-of-window high word instead of failing.
    let err = decode(&pair[..12], 0, 0x1000, 8).err().expect("a cut pair must be refused");
    assert!(err.contains("lddw"), "{err}");
}

#[test]
fn decode_still_accepts_plain_eight_byte_windows() {
    let bytes = [0x95u8, 0, 0, 0, 0, 0, 0, 0];
    let insns = decode(&bytes, 0, 0x1000, 8).expect("exit decodes");
    assert_eq!(insns.len(), 1);
    assert_eq!(render(insns[0], &bytes, 0), "exit");
}

#[test]
fn decode_still_refuses_unknown_opcodes() {
    let bytes = [0xffu8, 0, 0, 0, 0, 0, 0, 0];
    let err = decode(&bytes, 0, 0x1000, 8).err().expect("unknown opcode must be refused");
    assert!(err.contains("unknown opcode"), "{err}");
}
