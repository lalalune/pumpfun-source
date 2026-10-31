#!/usr/bin/env python3
"""Annotate the admin_cto window in the original or a candidate ELF.

Usage: annot.py <orig|unstripped.so> [--symbols unstripped.so]
The original capture has no candidate symbol table, so ``orig`` requires either
``--symbols`` or ``PUMP_ADMIN_CTO_SYMBOL_SO``. Candidate mode defaults to the
candidate ELF itself. Output is ``off text ; label``.
"""
import argparse
import os
import re
import sys


def symbol_path(subject, explicit=None, environ=None):
    environ = os.environ if environ is None else environ
    selected = explicit or environ.get("PUMP_ADMIN_CTO_SYMBOL_SO")
    if selected:
        return selected
    if subject != "orig":
        return subject
    raise ValueError("orig requires --symbols or PUMP_ADMIN_CTO_SYMBOL_SO")


H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../harness")
sys.path.insert(0, H)
from score import original_windows, BASE
from win import Cand, insns, demangle, ORIG_SECS, objdump_text, resolve_original


def short(n):
    n = re.sub(r"<[^<>]*>", "", n)
    n = re.sub(r"<[^<>]*>", "", n)
    return "::".join(n.split("::")[-2:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", help="'orig' or a candidate unstripped ELF")
    parser.add_argument(
        "--symbols", help="candidate unstripped ELF used to name call targets"
    )
    args = parser.parse_args()
    arg = args.subject
    try:
        symso = symbol_path(arg, args.symbols)
    except ValueError as exc:
        parser.error(str(exc))
    symc = Cand(symso)
    names = {s: demangle(nm) for s, n, nm in symc.funcs}
    if arg == "orig":
        w = {x["start"]: x for x in original_windows()}[0x22A10]
        st = 0x22A10
        instructions = insns(w["raw"], st, ORIG_SECS)
        text = objdump_text(resolve_original(BASE / "original.so"), st, st + 27400)
    else:
        candidate = Cand(arg)
        s, n, nm = [
            (s, n, nm)
            for s, n, nm in candidate.funcs
            if re.search(r"admin_cto::execute$", demangle(nm))
        ][0]
        st = s
        instructions = insns(candidate.fn(s, n), s, candidate.secs)
        text = candidate.disassembly(s, n)
    for address, raw, _ in instructions:
        instruction = text.get(address, "")
        label = ""
        if raw[0] == 0x85:
            immediate = int.from_bytes(raw[4:8], "little", signed=True)
            target = address + 8 + immediate * 8
            if target in names:
                label = short(names[target])
            elif raw[1] == 0:
                label = "syscall"
        print(
            f"{address - st:05x} {instruction}"
            + (f" ; {label}" if label else "")
        )


if __name__ == "__main__":
    main()
