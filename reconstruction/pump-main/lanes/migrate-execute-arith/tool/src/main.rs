//! Static census of one SBF window of a committed capture.
//!
//! Usage:
//!   sbf_census <capture.so> <capture.json> <vaddr> <length> <listing-out> <census-out>
//!
//! Verifies the capture's SHA-256 against the `payload_sha256` recorded in the
//! capture's `capture.json`, maps the virtual address through the ELF `PT_LOAD`
//! headers, decodes the window with the standard eBPF/SBF encoding (register
//! jumps included, `lddw` paired), classifies the arithmetic shapes and writes
//! the listing and census JSON directly to the given paths. All failure paths
//! return non-zero exits; nothing is executed from the capture.

use std::env;
use std::fs;
use std::process::ExitCode;

const WINDOW_SOURCE: &str =
    "reconstruction/pump-main/prior-swarm/TARGETS-20261029.json (migrate_v2::execute)";

fn sha256(data: &[u8]) -> [u8; 32] {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let bitlen = (data.len() as u64) * 8;
    let mut padded = data.to_vec();
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bitlen.to_be_bytes());
    for block in padded.chunks(64) {
        let mut w = [0u32; 64];
        for (i, chunk) in block.chunks(4).enumerate() {
            w[i] = u32::from_be_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

fn expect_seal(data: &[u8], capture_json: &str) -> Result<String, String> {
    let key = "\"payload_sha256\"";
    let at = capture_json
        .find(key)
        .ok_or("capture.json has no payload_sha256 key")?;
    let colon = capture_json[at..]
        .find(':')
        .ok_or("payload_sha256 has no colon")?;
    let rest = &capture_json[at + colon..];
    let quote = rest.find('"').ok_or("payload_sha256 value is not quoted")?;
    let rest = &rest[quote + 1..];
    let end = rest.find('"').ok_or("payload_sha256 value is unterminated")?;
    let expected = &rest[..end];
    if expected.len() != 64 || !expected.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("payload_sha256 is not a 64-hex digest".to_string());
    }
    let digest = sha256(data);
    let actual: String = digest.iter().map(|b| format!("{b:02x}")).collect();
    if !actual.eq_ignore_ascii_case(expected) {
        return Err(format!(
            "capture sha256 {actual} does not match its capture.json seal {expected}"
        ));
    }
    Ok(actual)
}

fn vaddr_to_offset(data: &[u8], vaddr: u64) -> Result<u64, String> {
    if data.len() < 64 || &data[0..4] != b"\x7fELF" {
        return Err("capture is not an ELF image".to_string());
    }
    if data[4] != 2 {
        return Err("capture is not a 64-bit ELF".to_string());
    }
    let e_phoff = u64::from_le_bytes(data[32..40].try_into().unwrap());
    let e_phentsize = u16::from_le_bytes(data[54..56].try_into().unwrap()) as u64;
    let e_phnum = u16::from_le_bytes(data[56..58].try_into().unwrap()) as u64;
    for index in 0..e_phnum {
        let base = (e_phoff + index * e_phentsize) as usize;
        if base + e_phentsize as usize > data.len() || e_phentsize < 56 {
            return Err("truncated ELF program header".to_string());
        }
        let p_type = u32::from_le_bytes(data[base..base + 4].try_into().unwrap());
        let p_offset = u64::from_le_bytes(data[base + 8..base + 16].try_into().unwrap());
        let p_vaddr = u64::from_le_bytes(data[base + 16..base + 24].try_into().unwrap());
        let p_filesz = u64::from_le_bytes(data[base + 32..base + 40].try_into().unwrap());
        if p_type != 1 {
            continue; // PT_LOAD
        }
        if p_vaddr <= vaddr && vaddr < p_vaddr.saturating_add(p_filesz) {
            return Ok(p_offset + (vaddr - p_vaddr));
        }
    }
    Err(format!("virtual address {vaddr:#x} is not inside any PT_LOAD segment"))
}

#[derive(Clone, Copy)]
struct Insn {
    vaddr: u64,
    opcode: u8,
    dst: u8,
    src: u8,
    off: i16,
    imm: u32,
}

static ALU64_IMM: [(u8, &str); 12] = [
    (0x07, "add"), (0x17, "sub"), (0x27, "mul"), (0x37, "div"), (0x47, "or"),
    (0x57, "and"), (0x67, "lsh"), (0x77, "rsh"), (0x97, "mod"), (0xa7, "xor"),
    (0xb7, "mov"), (0xc7, "arsh"),
];
static ALU64_REG: [(u8, &str); 12] = [
    (0x0f, "add"), (0x1f, "sub"), (0x2f, "mul"), (0x3f, "div"), (0x4f, "or"),
    (0x5f, "and"), (0x6f, "lsh"), (0x7f, "rsh"), (0x9f, "mod"), (0xaf, "xor"),
    (0xbf, "mov"), (0xcf, "arsh"),
];
static ALU32_IMM: [(u8, &str); 12] = [
    (0x04, "add32"), (0x14, "sub32"), (0x24, "mul32"), (0x34, "div32"), (0x44, "or32"),
    (0x54, "and32"), (0x64, "lsh32"), (0x74, "rsh32"), (0x94, "mod32"), (0xa4, "xor32"),
    (0xb4, "mov32"), (0xc4, "arsh32"),
];
static ALU32_REG: [(u8, &str); 12] = [
    (0x0c, "add32"), (0x1c, "sub32"), (0x2c, "mul32"), (0x3c, "div32"), (0x4c, "or32"),
    (0x5c, "and32"), (0x6c, "lsh32"), (0x7c, "rsh32"), (0x9c, "mod32"), (0xac, "xor32"),
    (0xbc, "mov32"), (0xcc, "arsh32"),
];
static JMP_IMM: [(u8, &str); 12] = [
    (0x05, "ja"), (0x15, "jeq"), (0x25, "jgt"), (0x35, "jge"), (0x45, "jset"),
    (0x55, "jne"), (0x65, "jsgt"), (0x75, "jsge"), (0xa5, "jlt"), (0xb5, "jle"),
    (0xc5, "jslt"), (0xd5, "jsle"),
];
static JMP_REG: [(u8, &str); 12] = [
    (0x0d, "ja"), (0x1d, "jeq"), (0x2d, "jgt"), (0x3d, "jge"), (0x4d, "jset"),
    (0x5d, "jne"), (0x6d, "jsgt"), (0x7d, "jsge"), (0xad, "jlt"), (0xbd, "jle"),
    (0xcd, "jslt"), (0xdd, "jsle"),
];
static LDX: [(u8, &str); 4] = [(0x61, "ldxw"), (0x69, "ldxh"), (0x71, "ldxb"), (0x79, "ldxdw")];
static STX: [(u8, &str); 4] = [(0x63, "stxw"), (0x6b, "stxh"), (0x73, "stxb"), (0x7b, "stxdw")];
static ST: [(u8, &str); 4] = [(0x62, "stw"), (0x6a, "sth"), (0x72, "stb"), (0x7a, "stdw")];

fn table_lookup(table: &'static [(u8, &'static str)], op: u8) -> Option<&'static str> {
    table.iter().find(|(code, _)| *code == op).map(|(_, name)| *name)
}

fn mnemonic(op: u8) -> Option<&'static str> {
    if op == 0x18 {
        return Some("lddw");
    }
    if op == 0x85 {
        return Some("call");
    }
    if op == 0x95 {
        return Some("exit");
    }
    table_lookup(&ALU64_IMM, op)
        .or_else(|| table_lookup(&ALU64_REG, op))
        .or_else(|| table_lookup(&ALU32_IMM, op))
        .or_else(|| table_lookup(&ALU32_REG, op))
        .or_else(|| table_lookup(&JMP_IMM, op))
        .or_else(|| table_lookup(&JMP_REG, op))
        .or_else(|| table_lookup(&LDX, op))
        .or_else(|| table_lookup(&STX, op))
        .or_else(|| table_lookup(&ST, op))
}

fn render(ins: Insn, data: &[u8], offset: u64) -> String {
    let Insn { vaddr: _, opcode: op, dst, src, off, imm } = ins;
    let uimm = imm;
    match op {
        0x18 => {
            let hi = u32::from_le_bytes(
                data[(offset + 12) as usize..(offset + 16) as usize].try_into().unwrap(),
            );
            format!("lddw r{dst}, {:#x}", (imm as u64) | ((hi as u64) << 32))
        }
        0x85 => format!("call {}", imm),
        0x95 => "exit".to_string(),
        0x87 => format!("neg r{dst}"),
        0x84 => format!("neg32 r{dst}"),
        _ => {
            let name = mnemonic(op).expect("caller only passes known opcodes");
            if table_lookup(&ALU64_IMM, op).is_some() || table_lookup(&ALU32_IMM, op).is_some() {
                format!("{name} r{dst}, {uimm}")
            } else if table_lookup(&ALU64_REG, op).is_some() || table_lookup(&ALU32_REG, op).is_some() {
                format!("{name} r{dst}, r{src}")
            } else if table_lookup(&JMP_IMM, op).is_some() {
                if name == "ja" {
                    format!("ja {off:+}")
                } else {
                    format!("{name} r{dst}, {uimm}, {off:+}")
                }
            } else if table_lookup(&JMP_REG, op).is_some() {
                if name == "ja" {
                    format!("ja {off:+}")
                } else {
                    format!("{name} r{dst}, r{src}, {off:+}")
                }
            } else if table_lookup(&LDX, op).is_some() {
                format!("{name} r{dst}, [r{src}{off:+}]")
            } else if table_lookup(&STX, op).is_some() {
                format!("{name} [r{dst}{off:+}], r{src}")
            } else {
                format!("{name} [r{dst}{off:+}], {uimm}")
            }
        }
    }
}

/// op -> ("name", width) for the arithmetic opcodes the census tracks.
fn arith_op(op: u8) -> Option<(String, &'static str)> {
    let (name, width) = table_lookup(&ALU64_IMM, op)
        .map(|n| (n, "64"))
        .or_else(|| table_lookup(&ALU64_REG, op).map(|n| (n, "64")))
        .or_else(|| table_lookup(&ALU32_IMM, op).map(|n| (n, "32")))
        .or_else(|| table_lookup(&ALU32_REG, op).map(|n| (n, "32")))?;
    if matches!(name, "add" | "sub" | "mul" | "div" | "mod") {
        Some((format!("{name}{width}"), width))
    } else {
        None
    }
}

fn is_unsigned_guard(op: u8) -> bool {
    matches!(mnemonic(op), Some("jgt") | Some("jge") | Some("jlt") | Some("jle"))
}

fn census(insns: &[Insn], data: &[u8], offset: u64, vaddr: u64) -> serde_style::Census {
    let mut histogram: Vec<(String, u32)> = Vec::new();
    let mut checked = Vec::new();
    let mut saturating = Vec::new();
    let mut error_constants = Vec::new();
    let mut constants: Vec<(u32, u64)> = Vec::new();
    let mut division = Vec::new();
    for (index, ins) in insns.iter().enumerate() {
        let name = match mnemonic(ins.opcode) {
            Some(n) => n.to_string(),
            None => format!("op_{:#04x}", ins.opcode), // decode() refuses unknowns already
        };
        if let Some(entry) = histogram.iter_mut().find(|(k, _)| *k == name) {
            entry.1 += 1;
        } else {
            histogram.push((name.to_string(), 1));
        }

        if ins.opcode == 0x18 {
            // The high word of an lddw sits in the paired slot 12 bytes into
            // the 16-byte instruction; derive it from the instruction's own
            // address, not an instruction index (lddw slots are 16 bytes).
            let hi_at = offset + (ins.vaddr - vaddr) + 12;
            let hi = u32::from_le_bytes(data[hi_at as usize..hi_at as usize + 4].try_into().unwrap());
            let full = (ins.imm as u64) | ((hi as u64) << 32);
            let low32 = full & 0xFFFFFFFF;
            if (6000..7000).contains(&low32) {
                error_constants.push(format!("{:#x}: lddw {full:#x}", ins.vaddr));
            }
            if !constants.iter().any(|(v, _)| *v == ins.imm) {
                constants.push((ins.imm, ins.vaddr));
            }
        }
        if ins.opcode == 0xb7 && (6000..7000).contains(&(ins.imm)) {
            error_constants.push(format!("{:#x}: mov {}", ins.vaddr, ins.imm));
        }
        if matches!(ins.opcode, 0x62 | 0x7a | 0x72 | 0x6a) && (6000..7000).contains(&(ins.imm)) {
            let width = match ins.opcode {
                0x62 => "stw32",
                0x7a => "stdw64",
                0x72 => "stb8",
                _ => "sth16",
            };
            error_constants.push(format!("{:#x}: store {} {}", ins.vaddr, width, ins.imm));
        }

        if let Some((opname, _width)) = arith_op(ins.opcode) {
            if matches!(opname.as_str(), "add64" | "sub64" | "add32" | "sub32") {
                let form = if table_lookup(&ALU64_IMM, ins.opcode).is_some()
                    || table_lookup(&ALU32_IMM, ins.opcode).is_some()
                {
                    "imm"
                } else {
                    "reg"
                };
                let guard = insns[index + 1..(index + 5).min(insns.len())]
                    .iter()
                    .find(|c| is_unsigned_guard(c.opcode));
                if let Some(guard) = guard {
                    let gname = mnemonic(guard.opcode).unwrap();
                    let gform = if table_lookup(&JMP_IMM, guard.opcode).is_some() { "imm" } else { "reg" };
                    checked.push(format!(
                        "{:#x}: {} {} guarded by {}({}) @ {:#x}",
                        ins.vaddr, opname, form, gname, gform, guard.vaddr
                    ));
                }
                if let Some(guard) = insns.get(index + 1) {
                    if guard.off == 2 && is_unsigned_guard(guard.opcode) {
                        saturating.push(format!(
                            "{:#x}: {} guard skips {} @ {:#x}",
                            guard.vaddr,
                            mnemonic(guard.opcode).unwrap(),
                            opname,
                            ins.vaddr
                        ));
                    }
                }
            }
        }
        if let Some((opname, _)) = arith_op(ins.opcode) {
            if matches!(opname.as_str(), "mul64" | "div64" | "mod64" | "mul32" | "div32" | "mod32") {
                division.push(format!("{:#x}: {}", ins.vaddr, opname));
            }
        }
    }
    serde_style::Census {
        instruction_count: insns.len(),
        histogram,
        checked,
        saturating,
        error_constants,
        constants,
        division,
        call_sites: insns.iter().filter(|i| i.opcode == 0x85).count(),
        exit_sites: insns.iter().filter(|i| i.opcode == 0x95).count(),
        window_source: WINDOW_SOURCE.to_string(),
    }
}

/// Tiny helpers so the tool has zero external dependencies while still
/// emitting structured JSON.
mod serde_style {
    pub struct Census {
        pub instruction_count: usize,
        pub histogram: Vec<(String, u32)>,
        pub checked: Vec<String>,
        pub saturating: Vec<String>,
        pub error_constants: Vec<String>,
        pub constants: Vec<(u32, u64)>,
        pub division: Vec<String>,
        pub call_sites: usize,
        pub exit_sites: usize,
        pub window_source: String,
    }

    impl Census {
        pub fn to_json(&self, window: (u64, u64), capture_sha: &str, listing: &str) -> String {
            let mut s = String::new();
            s.push_str("{\n");
            s.push_str(&format!(" \"capture_sha256\": \"{capture_sha}\",\n"));
            s.push_str(&format!(
                " \"window\": {{\"vaddr\": \"{:#x}\", \"bytes\": {}, \"source\": \"{}\"}},\n",
                window.0, window.1, self.window_source
            ));
            s.push_str(&format!(" \"instruction_count\": {},\n", self.instruction_count));
            s.push_str(" \"opcode_histogram\": {");
            let hist: Vec<String> = self.histogram.iter().map(|(k, v)| format!("\"{k}\": {v}")).collect();
            s.push_str(&hist.join(", "));
            s.push_str("},\n");
            let list = |items: &[String]| {
                let quoted: Vec<String> = items.iter().map(|i| format!("\"{i}\"")).collect();
                format!("[{}]", quoted.join(", "))
            };
            s.push_str(&format!(" \"checked_arithmetic_sites\": {},\n", list(&self.checked)));
            s.push_str(&format!(" \"saturating_arithmetic_sites\": {},\n", list(&self.saturating)));
            s.push_str(&format!(" \"error_code_constants\": {},\n", list(&self.error_constants)));
            let consts: Vec<String> = self
                .constants
                .iter()
                .map(|(v, a)| format!("\"{v:#x}\": \"{a:#x}\""))
                .collect();
            s.push_str(&format!(" \"32bit_lddw_constants\": {{{}}},\n", consts.join(", ")));
            s.push_str(&format!(" \"division_multiplication_sites\": {},\n", list(&self.division)));
            s.push_str(&format!(" \"call_sites\": {},\n", self.call_sites));
            s.push_str(&format!(" \"exit_sites\": {},\n", self.exit_sites));
            s.push_str(&format!(" \"listing\": \"{listing}\"\n"));
            s.push_str("}\n");
            s
        }
    }
}

fn decode(data: &[u8], offset: u64, vaddr: u64, length: u64) -> Result<Vec<Insn>, String> {
    if length % 8 != 0 {
        return Err(format!("window length {length} is not a multiple of 8"));
    }
    if (offset + length) as usize > data.len() {
        return Err("window extends past end of file".to_string());
    }
    let mut insns = Vec::new();
    let mut i = 0u64;
    while i < length {
        let at = (offset + i) as usize;
        let op = data[at];
        let regs = data[at + 1];
        let off = i16::from_le_bytes(data[at + 2..at + 4].try_into().unwrap());
        let imm = u32::from_le_bytes(data[at + 4..at + 8].try_into().unwrap());
        let ins = Insn { vaddr: vaddr + i, opcode: op, dst: regs & 0x0F, src: regs >> 4, off, imm };
        if mnemonic(op).is_none() && op != 0x00 {
            return Err(format!("unknown opcode {op:#04x} at {:#x}; refusing to census a misdecoded stream", ins.vaddr));
        }
        let _ = render(ins, data, offset + i);
        insns.push(ins);
        i += if op == 0x18 { 16 } else { 8 };
    }
    Ok(insns)
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() != 7 {
        eprintln!("usage: sbf_census <capture.so> <capture.json> <vaddr> <length> <listing-out> <census-out>");
        return ExitCode::from(2);
    }
    let data = match fs::read(&args[1]) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("reading capture failed: {e}");
            return ExitCode::FAILURE;
        }
    };
    let capture_json = match fs::read_to_string(&args[2]) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("reading capture.json failed: {e}");
            return ExitCode::FAILURE;
        }
    };
    let seal = match expect_seal(&data, &capture_json) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("seal check failed: {e}");
            return ExitCode::FAILURE;
        }
    };
    let vaddr = match u64::from_str_radix(args[3].trim_start_matches("0x"), 16) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("bad vaddr: {e}");
            return ExitCode::FAILURE;
        }
    };
    let length: u64 = match args[4].parse() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("bad length: {e}");
            return ExitCode::FAILURE;
        }
    };
    let offset = match vaddr_to_offset(&data, vaddr) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("{e}");
            return ExitCode::FAILURE;
        }
    };
    let insns = match decode(&data, offset, vaddr, length) {
        Ok(i) => i,
        Err(e) => {
            eprintln!("decode failed: {e}");
            return ExitCode::FAILURE;
        }
    };
    let mut listing = String::new();
    for ins in &insns {
        listing.push_str(&format!("{:06x}  {}\n", ins.vaddr, render(*ins, &data, offset + (ins.vaddr - vaddr))));
    }
    if let Err(e) = fs::write(&args[5], listing) {
        eprintln!("writing listing failed: {e}");
        return ExitCode::FAILURE;
    }
    let report = census(&insns, &data, offset, vaddr);
    let listing_ref = args[5].replace('\\', "/");
    let json = report.to_json((vaddr, length), &seal, &listing_ref);
    if let Err(e) = fs::write(&args[6], json) {
        eprintln!("writing census failed: {e}");
        return ExitCode::FAILURE;
    }
    println!("census written: {} instructions", insns.len());
    ExitCode::SUCCESS
}
