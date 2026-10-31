//! The seven Anchor IDL commands of Pump Main. They are not in the published
//! IDL: instruction data starting with the tag `40f4bc78a7e9690a` reaches
//! Anchor's generated `IdlInstruction` dispatcher, and the captured program
//! still carries it.
//!
//! A pure model of the decode, the account checks in their order, the System
//! Program calls the commands make and the account state they leave. Checked
//! against the captured Pump program by `tests/test_anchor_idl_captured.py`
//! on the inputs listed there; that is matching behaviour on those inputs,
//! not a byte-identity claim. Unconfirmed: the 10 MiB account limit on a
//! resize (no case grows an account that far).

/// Anchor error numbers.
pub const DID_NOT_DESERIALIZE: u32 = 102;
pub const IDL_INVALID_PROGRAM: u32 = 1001;
pub const IDL_NOT_EMPTY: u32 = 1002;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_HAS_ONE: u32 = 2001;
pub const CONSTRAINT_SIGNER: u32 = 2002;
pub const CONSTRAINT_RAW: u32 = 2003;
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_EXECUTABLE: u32 = 2007;
pub const CONSTRAINT_ZERO: u32 = 2013;
pub const CONSTRAINT_CLOSE: u32 = 2011;
pub const REQUIRE_GTE: u32 = 2506;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const NOT_ENOUGH_KEYS: u32 = 3005;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
/// System Program error numbers.
pub const SYSTEM_ACCOUNT_IN_USE: u32 = 0;
pub const SYSTEM_RESULT_WITH_NEGATIVE_LAMPORTS: u32 = 1;

pub type Key = [u8; 32];
pub const SYSTEM: Key = [0; 32];
/// The first eight bytes of an `IdlAccount`.
pub const IDL_DISCRIMINATOR: [u8; 8] = [24, 70, 98, 191, 58, 144, 123, 158];
/// Discriminator, authority and `data_len`.
pub const HEADER_LEN: usize = 44;
/// `create` and `resize` add at most this many bytes.
pub const MAX_STEP: u64 = 10_000;

/// `write` allocates its stated length before reading it; the heap holds this
/// many bytes less what the account slots of the instruction already took.
pub const WRITE_HEAP: u64 = 32_030;
pub const FIRST_SLOT_HEAP: u64 = 120;
pub const REPEATED_SLOT_HEAP: u64 = 48;

/// Rent-exempt minimum for `len` data bytes at the default rent.
pub fn rent(len: u64) -> u64 {
    (len + 128) * 6_960
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Owner {
    System,
    Pump,
    Other,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Account {
    pub key: Key,
    pub signer: bool,
    pub writable: bool,
    pub owner: Owner,
    pub lamports: u64,
    pub executable: bool,
    pub data: Vec<u8>,
}

/// The derived keys a command compares against.
#[derive(Clone, Copy, Debug)]
pub struct Keys {
    pub pump: Key,
    pub base: Key,
    pub canonical: Key,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Failure {
    /// A custom error and the account the Anchor log names, if any.
    Code(u32, Option<&'static str>),
    /// A System Program custom error raised inside the CPI.
    System(u32),
    /// An `InstructionError` with no number.
    Runtime(&'static str),
    Panic,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Done {
    /// The `Instruction: ...` log line.
    pub log: &'static str,
    /// Every distinct account after the call, in first-slot order.
    pub accounts: Vec<Account>,
}

type Step<T> = Result<T, Failure>;

fn code<T>(number: u32) -> Step<T> {
    Err(Failure::Code(number, None))
}

fn named<T>(number: u32, name: &'static str) -> Step<T> {
    Err(Failure::Code(number, Some(name)))
}

fn require(ok: bool, number: u32, name: &'static str) -> Step<()> {
    if ok {
        Ok(())
    } else {
        named(number, name)
    }
}

enum Command {
    Create(u64),
    CreateBuffer,
    Write(Vec<u8>),
    SetBuffer,
    SetAuthority(Key),
    Close,
    Resize(u64),
}

/// Reads a prefix: bytes after the arguments are ignored.
fn decode(data: &[u8], heap_left: u64) -> Step<Command> {
    let bad = Failure::Code(DID_NOT_DESERIALIZE, None);
    let (&tag, tail) = data.split_first().ok_or(bad.clone())?;
    let number = || -> Step<u64> {
        let bytes = tail.get(..8).ok_or(bad.clone())?;
        Ok(u64::from_le_bytes(bytes.try_into().unwrap()))
    };
    Ok(match tag {
        0 => Command::Create(number()?),
        1 => Command::CreateBuffer,
        2 => {
            let bytes = tail.get(..4).ok_or(bad.clone())?;
            let len = u32::from_le_bytes(bytes.try_into().unwrap()) as usize;
            if len as u64 > heap_left {
                return Err(Failure::Panic);
            }
            Command::Write(tail[4..].get(..len).ok_or(bad)?.to_vec())
        }
        3 => Command::SetBuffer,
        4 => Command::SetAuthority(tail.get(..32).ok_or(bad)?.try_into().unwrap()),
        5 => Command::Close,
        6 => Command::Resize(number()?),
        _ => return Err(bad),
    })
}

struct Header {
    authority: Key,
    data_len: u32,
}

fn stored_header(data: &[u8]) -> Step<Header> {
    let Some(bytes) = data.get(8..HEADER_LEN) else {
        return code(ACCOUNT_DID_NOT_DESERIALIZE);
    };
    Ok(Header {
        authority: bytes[..32].try_into().unwrap(),
        data_len: u32::from_le_bytes(bytes[32..].try_into().unwrap()),
    })
}

fn put_header(data: &mut [u8], header: &Header) {
    data[..8].copy_from_slice(&IDL_DISCRIMINATOR);
    data[8..40].copy_from_slice(&header.authority);
    data[40..HEADER_LEN].copy_from_slice(&header.data_len.to_le_bytes());
}

/// A transaction merges the privileges of one key over all its slots.
struct Slots {
    world: Vec<Account>,
    index: Vec<usize>,
    next: usize,
}

impl Slots {
    fn new(slots: &[Account]) -> Self {
        let mut world: Vec<Account> = Vec::new();
        let mut index = Vec::new();
        for slot in slots {
            match world.iter().position(|a| a.key == slot.key) {
                Some(at) => {
                    world[at].signer |= slot.signer;
                    world[at].writable |= slot.writable;
                    index.push(at);
                }
                None => {
                    index.push(world.len());
                    world.push(slot.clone());
                }
            }
        }
        Self { world, index, next: 0 }
    }

    fn raw(&mut self, name: Option<&'static str>) -> Step<usize> {
        let Some(&at) = self.index.get(self.next) else {
            return Err(Failure::Code(NOT_ENOUGH_KEYS, name));
        };
        self.next += 1;
        Ok(at)
    }

    fn signer(&mut self, name: &'static str) -> Step<usize> {
        let at = self.raw(Some(name))?;
        require(self.world[at].signer, ACCOUNT_NOT_SIGNER, name)?;
        Ok(at)
    }

    fn system(&mut self) -> Step<usize> {
        let at = self.raw(Some("system_program"))?;
        require(self.world[at].key == SYSTEM, INVALID_PROGRAM_ID, "system_program")?;
        Ok(at)
    }

    /// `Account<IdlAccount>`: owner, then discriminator, then the header.
    fn typed(&mut self, name: &'static str) -> Step<(usize, Header)> {
        let at = self.raw(Some(name))?;
        let header = self.load(at, name, true)?;
        Ok((at, header))
    }

    fn load(&self, at: usize, name: &'static str, checked: bool) -> Step<Header> {
        let account = &self.world[at];
        if account.owner == Owner::System && account.lamports == 0 {
            return named(ACCOUNT_NOT_INITIALIZED, name);
        }
        if account.owner != Owner::Pump {
            return named(OWNED_BY_WRONG_PROGRAM, name);
        }
        if checked {
            if account.data.len() < 8 {
                return named(DISCRIMINATOR_NOT_FOUND, name);
            }
            if account.data[..8] != IDL_DISCRIMINATOR {
                return named(DISCRIMINATOR_MISMATCH, name);
            }
        }
        stored_header(&account.data).map_err(|_| Failure::Code(ACCOUNT_DID_NOT_DESERIALIZE, Some(name)))
    }

    fn writable(&self, at: usize, name: &'static str) -> Step<()> {
        require(self.world[at].writable, CONSTRAINT_MUT, name)
    }

    fn has_authority(&self, header: &Header, authority: usize, name: &'static str) -> Step<()> {
        require(header.authority == self.world[authority].key, CONSTRAINT_HAS_ONE, name)
    }

    fn active(&self, authority: usize) -> Step<()> {
        require(self.world[authority].key != SYSTEM, CONSTRAINT_RAW, "authority")
    }

    fn finish(self, log: &'static str) -> Step<Done> {
        Ok(Done { log, accounts: self.world })
    }
}

/// `system_instruction::transfer` run by the System Program, `to` writable.
fn system_transfer(world: &mut [Account], from: usize, to: usize, amount: u64) -> Step<()> {
    if !world[from].writable {
        return Err(Failure::Runtime("PrivilegeEscalation"));
    }
    if !world[from].data.is_empty() {
        return Err(Failure::Runtime("InvalidArgument"));
    }
    if world[from].lamports < amount {
        return Err(Failure::System(SYSTEM_RESULT_WITH_NEGATIVE_LAMPORTS));
    }
    if world[from].owner != Owner::System && amount > 0 {
        return Err(Failure::Runtime("ExternalAccountLamportSpend"));
    }
    world[from].lamports -= amount;
    world[to].lamports += amount;
    Ok(())
}

fn create(keys: &Keys, slots: &[Account], requested: u64) -> Step<Done> {
    let mut s = Slots::new(slots);
    let from = s.raw(Some("from"))?;
    let to = s.raw(Some("to"))?;
    let base = s.raw(Some("base"))?;
    s.system()?;
    let program = s.raw(Some("program"))?;
    require(s.world[from].signer, CONSTRAINT_SIGNER, "from")?;
    s.writable(to, "to")?;
    require(s.world[base].key == keys.base, CONSTRAINT_SEEDS, "base")?;
    require(s.world[program].executable, CONSTRAINT_EXECUTABLE, "program")?;
    if s.world[program].key != keys.pump {
        return code(IDL_INVALID_PROGRAM);
    }
    let Some(space) = requested.checked_add(HEADER_LEN as u64) else {
        return Err(Failure::Panic);
    };
    let space = space.min(MAX_STEP);
    // The address is derived, not read from `to`; the CPI cannot find it in
    // the accounts it was handed unless `to` is that address.
    if s.world[to].key != keys.canonical {
        return Err(Failure::Runtime("MissingAccount"));
    }
    if !s.world[from].writable {
        return Err(Failure::Runtime("PrivilegeEscalation"));
    }
    if s.world[to].lamports > 0 || !s.world[to].data.is_empty() || s.world[to].owner != Owner::System {
        return Err(Failure::System(SYSTEM_ACCOUNT_IN_USE));
    }
    system_transfer(&mut s.world, from, to, rent(space))?;
    let authority = s.world[from].key;
    s.world[to].owner = Owner::Pump;
    s.world[to].data = vec![0; space as usize];
    put_header(&mut s.world[to].data, &Header { authority, data_len: 0 });
    s.finish("IdlCreateAccount")
}

fn create_buffer(slots: &[Account]) -> Step<Done> {
    let mut s = Slots::new(slots);
    let buffer = s.raw(None)?;
    let authority = s.signer("authority")?;
    // The `zero` check reads eight bytes before the owner is looked at.
    if s.world[buffer].data.len() < 8 {
        return Err(Failure::Panic);
    }
    if s.world[buffer].data[..8] != [0; 8] {
        return named(CONSTRAINT_ZERO, "buffer");
    }
    let header = s.load(buffer, "buffer", false)?;
    s.writable(buffer, "buffer")?;
    let size = s.world[buffer].data.len() as u64;
    require(s.world[buffer].lamports >= rent(size), CONSTRAINT_RENT_EXEMPT, "buffer")?;
    s.active(authority)?;
    let header = Header { authority: s.world[authority].key, data_len: header.data_len };
    put_header(&mut s.world[buffer].data, &header);
    s.finish("IdlCreateBuffer")
}

fn admit_idl(s: &mut Slots) -> Step<(usize, Header)> {
    let (idl, header) = s.typed("idl")?;
    let authority = s.signer("authority")?;
    s.writable(idl, "idl")?;
    s.has_authority(&header, authority, "idl")?;
    s.active(authority)?;
    Ok((idl, header))
}

fn write(slots: &[Account], input: &[u8]) -> Step<Done> {
    let mut s = Slots::new(slots);
    let (idl, mut header) = admit_idl(&mut s)?;
    let old = header.data_len as usize;
    let end = old + input.len();
    header.data_len = header.data_len.checked_add(input.len() as u32).ok_or(Failure::Panic)?;
    let body = &mut s.world[idl].data[HEADER_LEN..];
    if end > body.len() {
        return Err(Failure::Panic);
    }
    body[old..end].copy_from_slice(input);
    put_header(&mut s.world[idl].data, &header);
    s.finish("IdlWrite")
}

fn set_buffer(slots: &[Account]) -> Step<Done> {
    let mut s = Slots::new(slots);
    let (buffer, buffer_header) = s.typed("buffer")?;
    let (idl, idl_header) = s.typed("idl")?;
    let authority = s.signer("authority")?;
    s.writable(buffer, "buffer")?;
    require(buffer_header.authority == idl_header.authority, CONSTRAINT_RAW, "buffer")?;
    s.writable(idl, "idl")?;
    s.has_authority(&idl_header, authority, "idl")?;
    s.active(authority)?;
    if buffer == idl {
        // The source read cannot borrow the account the target holds mutably.
        return Err(Failure::Panic);
    }
    let len = buffer_header.data_len as usize;
    let Some(source) = s.world[buffer].data[HEADER_LEN..].get(..len).map(<[u8]>::to_vec) else {
        return Err(Failure::Panic);
    };
    if s.world[idl].data.len() - HEADER_LEN < len {
        return code(REQUIRE_GTE);
    }
    s.world[idl].data[HEADER_LEN..HEADER_LEN + len].copy_from_slice(&source);
    let header = Header { authority: idl_header.authority, data_len: buffer_header.data_len };
    put_header(&mut s.world[idl].data, &header);
    s.finish("IdlSetBuffer")
}

fn set_authority(slots: &[Account], new_authority: Key) -> Step<Done> {
    let mut s = Slots::new(slots);
    let (idl, header) = admit_idl(&mut s)?;
    put_header(&mut s.world[idl].data, &Header { authority: new_authority, data_len: header.data_len });
    s.finish("IdlSetAuthority")
}

fn close(slots: &[Account]) -> Step<Done> {
    let mut s = Slots::new(slots);
    let (account, header) = s.typed("account")?;
    let authority = s.signer("authority")?;
    let destination = s.raw(Some("sol_destination"))?;
    s.writable(account, "account")?;
    s.has_authority(&header, authority, "account")?;
    require(account != destination, CONSTRAINT_CLOSE, "account")?;
    s.active(authority)?;
    s.writable(destination, "sol_destination")?;
    let total = s.world[destination].lamports.checked_add(s.world[account].lamports).ok_or(Failure::Panic)?;
    s.world[destination].lamports = total;
    s.world[account].lamports = 0;
    s.world[account].owner = Owner::System;
    s.world[account].data.clear();
    s.finish("IdlCloseAccount")
}

fn resize(slots: &[Account], requested: u64) -> Step<Done> {
    let mut s = Slots::new(slots);
    let (idl, header) = s.typed("idl")?;
    let authority = s.signer("authority")?;
    s.system()?;
    s.writable(idl, "idl")?;
    s.has_authority(&header, authority, "idl")?;
    s.writable(authority, "authority")?;
    s.active(authority)?;
    if header.data_len != 0 {
        return code(IDL_NOT_EMPTY);
    }
    let current = s.world[idl].data.len() as u64;
    let Some(delta) = requested.checked_sub(current) else {
        return Err(Failure::Panic);
    };
    let new_len = current + delta.min(MAX_STEP);
    if new_len > current {
        let Some(amount) = rent(new_len).checked_sub(s.world[idl].lamports) else {
            return Err(Failure::Panic);
        };
        system_transfer(&mut s.world, authority, idl, amount)?;
        s.world[idl].data.resize(new_len as usize, 0);
    }
    put_header(&mut s.world[idl].data, &header);
    s.finish("IdlResizeAccount")
}

/// The check LiteSVM runs at the end of the transaction. An account with data
/// may stay below rent exemption only if it kept its size and gained nothing.
fn rent_state_ok(before: &Account, after: &Account) -> bool {
    let size = after.data.len() as u64;
    size == 0
        || after.lamports >= rent(size)
        || (before.data.len() as u64 == size && after.lamports <= before.lamports)
}

/// `args` is the instruction data after the eight-byte tag.
pub fn run(keys: &Keys, args: &[u8], slots: &[Account]) -> Result<Done, Failure> {
    let before = Slots::new(slots).world;
    let repeated = (slots.len() - before.len()) as u64;
    let heap_left = WRITE_HEAP - FIRST_SLOT_HEAP * before.len() as u64 - REPEATED_SLOT_HEAP * repeated;
    let done = command(keys, args, slots, heap_left)?;
    if before.iter().zip(&done.accounts).any(|(b, a)| !rent_state_ok(b, a)) {
        return Err(Failure::Runtime("InsufficientFundsForRent"));
    }
    Ok(done)
}

fn command(keys: &Keys, args: &[u8], slots: &[Account], heap_left: u64) -> Step<Done> {
    match decode(args, heap_left)? {
        Command::Create(size) => create(keys, slots, size),
        Command::CreateBuffer => create_buffer(slots),
        Command::Write(bytes) => write(slots, &bytes),
        Command::SetBuffer => set_buffer(slots),
        Command::SetAuthority(key) => set_authority(slots, key),
        Command::Close => close(slots),
        Command::Resize(size) => resize(slots, size),
    }
}
