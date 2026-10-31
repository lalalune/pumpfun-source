//! How Pump Main reads instruction data, before any account is looked at:
//! the eight-byte discriminators of all 56 published instructions, each
//! instruction's argument layout, and the `#[event_cpi]` entry.
//!
//! A pure model of which instruction data is refused and how. The Borsh rules
//! differ from the IDL in one place: `OptionBool` and `OptionU64` are read
//! from whatever is left, so trailing ones may be cut off. Checked against the
//! captured Pump program by `tests/test_instruction_data_captured.py` on the
//! inputs listed there; that is matching behaviour on those inputs, not a
//! byte-identity claim. The tag of the Anchor IDL commands is a separate entry
//! (`anchor_idl.rs`) and is not modelled here.

/// Anchor error numbers.
pub const FALLBACK_NOT_FOUND: u32 = 101;
pub const DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_SIGNER: u32 = 2002;
pub const CONSTRAINT_SEEDS: u32 = 2006;

/// Anchor's EVENT_IX_TAG in little-endian order.
pub const EVENT_TAG: [u8; 8] = [228, 69, 165, 46, 81, 203, 154, 29];

/// A `string` or `bytes` argument allocates its stated length before reading
/// it, from a heap holding this many bytes less what came before it.
pub const HEAP: u64 = 32_030;
pub const FIRST_SLOT_HEAP: u64 = 120;
pub const REPEATED_SLOT_HEAP: u64 = 48;

/// Discriminator and one code per argument: `u` u64 or i64, `k` pubkey, `b`
/// bool, `c` u8, `s` string, `x` bytes, `p` Option<u64>, `q` Option<bool>, `r`
/// Option<Pubkey>, `v` Vec<u64>, `o` OptionBool, `w` OptionU64.
pub const INSTRUCTIONS: [([u8; 8], &str); 56] = [
    ([2, 14, 61, 138, 170, 142, 14, 95], "ku"),
    ([111, 121, 21, 56, 40, 24, 94, 209], "k"),
    ([125, 126, 214, 134, 77, 229, 188, 89], "qpr"),
    ([8, 217, 96, 231, 144, 104, 192, 5], "k"),
    ([209, 11, 115, 87, 213, 23, 124, 204], "uuuuu"),
    ([102, 6, 61, 18, 1, 218, 235, 234], "uuoo"),
    ([194, 171, 28, 70, 104, 77, 91, 47], "uuo"),
    ([225, 247, 80, 30, 213, 179, 132, 136], "uuo"),
    ([56, 252, 116, 8, 158, 223, 205, 95], "uuoo"),
    ([184, 23, 238, 97, 103, 197, 211, 61], "uuo"),
    ([7, 5, 29, 196, 245, 23, 101, 80], "uuo"),
    ([37, 58, 35, 126, 190, 53, 228, 197], ""),
    ([122, 243, 204, 65, 94, 116, 29, 55], ""),
    ([16, 4, 71, 28, 204, 1, 40, 27], ""),
    ([249, 69, 164, 218, 150, 103, 84, 138], ""),
    ([20, 22, 86, 123, 198, 28, 219, 132], ""),
    ([207, 17, 138, 242, 4, 34, 19, 56], ""),
    ([24, 30, 200, 40, 5, 28, 7, 119], "sssk"),
    ([214, 144, 76, 236, 95, 139, 49, 180], "ssskbowo"),
    ([165, 114, 103, 0, 121, 206, 247, 81], ""),
    ([255, 203, 19, 79, 244, 68, 8, 159], "b"),
    ([98, 54, 145, 97, 2, 70, 173, 43], "v"),
    ([234, 102, 194, 203, 150, 72, 62, 229], ""),
    ([117, 225, 127, 202, 134, 95, 68, 35], ""),
    ([94, 6, 202, 115, 255, 96, 232, 183], ""),
    ([175, 175, 109, 31, 13, 152, 155, 237], ""),
    ([239, 73, 245, 173, 209, 177, 84, 66], ""),
    ([155, 234, 231, 146, 236, 158, 162, 30], ""),
    ([87, 124, 52, 191, 52, 38, 214, 232], ""),
    ([187, 203, 18, 31, 206, 237, 254, 41], ""),
    ([225, 154, 117, 22, 215, 86, 246, 103], "ux"),
    ([223, 7, 253, 26, 81, 165, 218, 166], "k"),
    ([177, 65, 223, 38, 88, 209, 158, 155], "k"),
    ([51, 230, 133, 164, 1, 127, 131, 173], "uu"),
    ([93, 246, 130, 60, 231, 233, 64, 178], "uu"),
    ([28, 146, 222, 119, 38, 196, 105, 213], "uu"),
    ([254, 148, 255, 112, 207, 142, 170, 165], "k"),
    ([32, 154, 152, 219, 142, 108, 218, 165], "c"),
    ([61, 169, 188, 191, 153, 149, 42, 97], ""),
    ([138, 96, 174, 217, 48, 85, 197, 246], ""),
    ([27, 234, 178, 52, 147, 2, 187, 141], "uuuuukbuukk"),
    ([62, 79, 161, 211, 165, 170, 214, 210], "k"),
    ([116, 220, 107, 83, 191, 44, 32, 73], "ku"),
    ([161, 195, 222, 165, 225, 101, 192, 62], "k"),
    ([111, 172, 162, 232, 114, 89, 213, 142], "k"),
    ([101, 135, 191, 104, 9, 88, 20, 96], "u"),
    ([32, 246, 191, 52, 8, 201, 73, 186], ""),
    ([8, 48, 190, 7, 182, 68, 183, 229], ""),
    ([86, 31, 192, 87, 163, 87, 79, 238], ""),
    ([115, 103, 224, 255, 189, 89, 86, 195], "b"),
    ([28, 255, 230, 240, 172, 107, 203, 171], "b"),
    ([1, 9, 111, 208, 100, 31, 255, 163], "b"),
    ([251, 224, 171, 146, 160, 26, 113, 233], "p"),
    ([61, 175, 160, 249, 66, 66, 136, 175], "bu"),
    ([227, 181, 74, 196, 208, 21, 97, 213], ""),
    ([225, 252, 66, 4, 199, 35, 236, 16], "bk"),
];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Dispatch and decode passed: the account checks come next.
    Passed,
    Error(u32),
    /// The allocator aborted the program.
    OutOfMemory,
    /// `#[event_cpi]` entry with no account.
    NotEnoughAccountKeys,
}

struct Reader<'a> {
    rest: &'a [u8],
    heap: u64,
}

impl<'a> Reader<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], Outcome> {
        if self.rest.len() < n {
            return Err(Outcome::Error(DID_NOT_DESERIALIZE));
        }
        let (head, tail) = self.rest.split_at(n);
        self.rest = tail;
        Ok(head)
    }

    fn flag(&mut self) -> Result<bool, Outcome> {
        match self.take(1)?[0] {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(Outcome::Error(DID_NOT_DESERIALIZE)),
        }
    }

    fn length(&mut self) -> Result<usize, Outcome> {
        Ok(u32::from_le_bytes(self.take(4)?.try_into().unwrap()) as usize)
    }

    fn allocated(&mut self) -> Result<&'a [u8], Outcome> {
        let len = self.length()?;
        if len as u64 > self.heap {
            return Err(Outcome::OutOfMemory);
        }
        self.heap -= len as u64;
        self.take(len)
    }

    fn argument(&mut self, code: char) -> Result<(), Outcome> {
        match code {
            'u' => drop(self.take(8)?),
            'k' => drop(self.take(32)?),
            'c' => drop(self.take(1)?),
            'b' => drop(self.flag()?),
            's' => {
                if std::str::from_utf8(self.allocated()?).is_err() {
                    return Err(Outcome::Error(DID_NOT_DESERIALIZE));
                }
            }
            'x' => drop(self.allocated()?),
            'p' => {
                if self.flag()? {
                    self.take(8)?;
                }
            }
            'q' => {
                if self.flag()? {
                    self.flag()?;
                }
            }
            'r' => {
                if self.flag()? {
                    self.take(32)?;
                }
            }
            'v' => {
                for _ in 0..self.length()? {
                    self.take(8)?;
                }
            }
            // The two tolerant wrappers: nothing left is not an error.
            'o' => {
                if !self.rest.is_empty() {
                    self.flag()?;
                }
            }
            'w' => {
                // A short read takes nothing: `OptionBool` after it sees these bytes.
                if self.rest.len() >= 8 {
                    self.take(8)?;
                }
            }
            _ => unreachable!(),
        }
        Ok(())
    }
}

fn event_entry(signers: &[(bool, bool)]) -> Outcome {
    match signers.first() {
        None => Outcome::NotEnoughAccountKeys,
        Some((false, _)) => Outcome::Error(CONSTRAINT_SIGNER),
        Some((true, false)) => Outcome::Error(CONSTRAINT_SEEDS),
        Some((true, true)) => Outcome::Passed,
    }
}

/// `accounts` is one `(signer, is_event_authority)` per slot; `repeated` says
/// how many of those slots repeat an earlier key.
pub fn read(data: &[u8], accounts: &[(bool, bool)], repeated: u64) -> Outcome {
    let Some(tag) = data.get(..8) else {
        return Outcome::Error(FALLBACK_NOT_FOUND);
    };
    if tag == EVENT_TAG {
        return event_entry(accounts);
    }
    let Some((_, codes)) = INSTRUCTIONS.iter().find(|(disc, _)| disc == tag) else {
        return Outcome::Error(FALLBACK_NOT_FOUND);
    };
    let distinct = accounts.len() as u64 - repeated;
    let heap = HEAP - FIRST_SLOT_HEAP * distinct - REPEATED_SLOT_HEAP * repeated;
    let mut reader = Reader { rest: &data[8..], heap };
    for code in codes.chars() {
        if let Err(outcome) = reader.argument(code) {
            return outcome;
        }
    }
    Outcome::Passed
}
