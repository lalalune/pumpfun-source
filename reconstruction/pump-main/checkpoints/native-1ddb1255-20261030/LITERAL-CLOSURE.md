# Frozen 1ddb control: literal closure outside admin CTO

This attachment describes **only** the independently reproduced control for
`1ddb12553ccdb4ed45407ffe53f12f4644be172a`, run `41065537974`.
It is not an assertion about later `main`, a new mechanism, a source change,
a matched-window gain, transaction equivalence, or security acceptance.

The control's selected source vector has **135 files**, aggregate
`6e061e8785371cbe427c8ff591bc1a35846deafad89b8d922137a6c52c5579b9`,
and stages 136 workspace files. It separately reproduces the compiler-file
hashes retained by the historical **133-file** pass-13 measurement. The two
source vectors are not relabelled as the same measurement: the current vector
also contains `recovered/v3_exact_quote.rs` and `recovered/v3_exact_quote_host.rs`.
The admission verifier qualifies source/build/scorer evidence; this attachment
only compares already emitted bytes. It never invokes the scorer or SDK.

| Frozen input/output | Bytes | SHA-256 |
| --- | ---: | --- |
| Original captured payload | 10,485,715 | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` |
| Original meaningful ELF | 1,934,800 | `05249b60f8ddf02a53d0f8a43980fde40cce33f73526355b4ef08e292279819f` |
| Actual stripped compiler file | 1,934,832 | `b1cc01495e331a220d1c150c9be21810f172118e45bc45201fe223a8bf783703` |
| Actual symbols compiler file, bound by admission | 2,665,760 | `481ba72865f36b52b3cc27e824ef3762a0baff5509c48135aa627fb927418c2b` |

The original has a separate **8,550,915-byte all-zero allocation suffix**.
That suffix alone is excluded. Internal zeros, alignment gaps, section names,
headers and relocation records remain part of the literal meaningful-ELF test.
No emitted ELF is normalized, aligned to another image, padded or rewritten.
The two meaningful files remain unequal.

## Complete positional byte result

The 1,035 original selected windows exactly tile `.text`:
file offsets/virtual addresses `[288, 1,792,496)`, **1,792,208 bytes**,
without gaps or overlaps. `admin_cto::execute` is
`[0x22a10, 0x29518)` (**27,400 bytes**).

All other **1,034 bodies / 1,764,808 code bytes are literally equal at their
original file offsets**. This is stronger than finding an equal body elsewhere
in a candidate symbol table. CTO contains **13,522 differing byte positions**.
Across both meaningful files, every one of **1,934,832 physical positions** is
examined; **23,426 positions differ or are absent**, including the 32 extra bytes.
The result includes every region, rather than stopping at the first mismatch.

The following payloads are literally equal:

| Section | Bytes | Original / candidate file offsets |
| --- | ---: | --- |
| `.rodata` | 32,031 | 1,792,496 / 1,792,496 |
| `.data.rel.ro` | 10,352 | 1,824,528 / 1,824,528 |
| `.dynsym` | 456 | 1,835,056 / 1,835,056 |
| `.dynstr` | 288 | 1,835,512 / 1,835,512 |
| `.shstrtab` | 72 | 1,934,152 / 1,934,184 |

## The extra 32 bytes

The original has **6,147** 16-byte `.rel.dyn` records; the candidate has
**6,149**. CTO contributes **87 / 89** records. After filtering records whose
`r_offset` lies in the CTO range, the remaining **6,060 complete records are
literally identical in the same sequence**. This checks both `r_offset` and
`r_info`, rather than only relocation class counts. All 74 removed and 76 added
records target CTO.

CTO's type-8 relocation sites decode as actual two-slot `lddw` instructions:
**84 original / 86 candidate**. Their complete loaded-address multisets differ
only at `.data.rel.ro+0x128` (address 1,824,824), **9 / 11 loads**. Every other
target multiplicity agrees. The historical attribution of that object to the
String `fmt::Write` vtable is credited below; this packet recovers no new private
source or source-level cause.

All metadata changes are bounded to the table's two extra records:

- `.rel.dyn` size and `DT_RELSZ`: **98,352 → 98,384**.
- Type-8 count / `DT_RELCOUNT`: **5,877 → 5,879**; type-10 count stays **270**.
- Read-only LOAD `p_filesz` / `p_memsz`: **99,096 → 99,128**.
- `e_shoff`: **1,934,224 → 1,934,256**.
- `.shstrtab` file offset advances by **32**; its payload is unchanged.

All 90 section-header fields were compared. Only `.rel.dyn.sh_size` and
`.shstrtab.sh_offset` differ. ELF identity and every other decoded ELF-header,
program-header and dynamic-record field agree. The literal comparison includes
the physical displacement of the section-name and section-header tables;
field attribution does not make those bytes equal.

## Existing mechanism and added evidence

Credit the earlier [#2253](https://github.com/lalalune/pumpfun-source/pull/2253)
ELF-metadata study, [#2370](https://github.com/lalalune/pumpfun-source/pull/2370),
[#2380](https://github.com/lalalune/pumpfun-source/pull/2380), and
[#2416](https://github.com/lalalune/pumpfun-source/pull/2416), whose retained
`w9r1-admincto-relocs` notes already explain the two extra vtable loads and
32-byte relocation consequence. **This is not a new mechanism.**

Those earlier checkpoints still had text-size/layout differences, an 86-byte
rodata permutation, and relocated pointer differences. This frozen control now
establishes complete positional code-byte equality outside CTO, literal equality of
all the data payloads above, and equality in sequence of every non-CTO relocation
record. It identifies no separate recipe/data/layout barrier beyond CTO's code
and its relocation sites. It does not prove that any future source change will
preserve this closure or that an exact CTO body automatically proves metadata
identity; the complete emitted ELF must still be compared.

## Portable attachment

`literal_closure.py` exports `verify_literal(repo, candidate)`. The checkpoint
admission verifier supplies its already authenticated, externally provided
stripped ELF after source/build admission and its single official score run.
This attachment makes no subprocess, network, Git, SDK or scorer calls and writes
no ELF. A CLI report uses exclusive creation, preserving an existing output:

```bash
python3 -B reconstruction/pump-main/checkpoints/native-1ddb1255-20261030/literal_closure.py \
  --repo '/path with spaces/frozen reference inputs' \
  --candidate '/path with spaces/external artifact/candidate.so' \
  --json '/new owned output/literal-closure.json'
```

The explicit reference root must contain the captured original,
`reconstruction/base/functions.tsv`, and frozen `scripts/analyze.py`.
The latter two small public files are pinned to 1ddb Git blobs and SHA-256
values in `DEPENDENCIES`; they may be projected by the parent verifier without
Git or a private-workspace fallback. The official `elf_layout` parser admits the
ELF structure. The symbols/compiler provenance belongs to admission, rather
than a second duplicated scorer in this attachment.

Earlier private original-only, historical-2b integration, and initially pending
current-control reports remain unchanged. The independent full source/build
admission was linked additively after it passed. This public attachment does not
retarget those historical or pending records.
