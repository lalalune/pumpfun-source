// Solana SBF fix-ups + decompile/export for Ghidra 12.2 headless (lane w17a01-ghidra-decomp).
//
// Import: raw image at base 0 (offset == vaddr for every LOAD segment), language eBPF:LE:64:default, -noanalysis.
// Args:   <factsDir> <outDir> <tag> <entry[,entry...]>      facts come from prep.py
//
// Fix-ups for what the stock eBPF module gets wrong on Solana SBF (v1, e_machine 263):
//   * sections: the raw block is split per ELF section with real permissions (.rodata read-only, so string and
//     pubkey constants resolve; .data.rel.ro writable so vtables are not folded).
//   * internal calls: SBF encodes them as `call imm` with src=1 and imm = pc-relative slots, which the stock
//     `CALL disp32` constructor already decodes (inst_next + imm*8); every target gets its real Rust name.
//   * syscalls: SBF encodes them as `call -1` (src=1) plus an R_BPF_64_32 relocation, which the stock module decodes
//     as a call to itself. Each site gets a primary CALL_OVERRIDE_UNCONDITIONAL reference to a named stub with a
//     Solana prototype (sol_log_, sol_invoke_signed_rust, abort, ...).
//   * noreturn: functions whose body has no `exit` (prep.py) are marked noreturn, so panics/aborts end blocks.
//   * lddw: R_BPF_64_RELATIVE immediates are image vaddrs; each gets a data reference, label and typed data.
//   * r10: the cspec already treats R10 as the stack pointer, so [r10 - X] become stack locals local_X.
//
// @category SBF
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.ApplyFunctionSignatureCmd;
import ghidra.app.decompiler.*;
import ghidra.app.decompiler.component.DecompilerUtils;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.pcode.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.util.CodeUnitInsertionException;
import ghidra.util.data.DataTypeParser;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class SbfDecomp extends GhidraScript {

    AddressSpace ram;
    Map<Long, String> funcNames = new HashMap<>();
    Set<Long> noret = new HashSet<>();
    Map<Long, String> labels = new HashMap<>();

    Address A(long v) { return ram.getAddress(v); }

    List<String[]> tsv(File f) throws IOException {
        List<String[]> rows = new ArrayList<>();
        if (!f.exists()) return rows;
        for (String l : Files.readAllLines(f.toPath())) if (!l.isEmpty()) rows.add(l.split("\t", -1));
        return rows;
    }

    static long hex(String s) { return Long.decode(s); }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File facts = new File(args[0]);
        File out = new File(args[1]);
        String tag = args[2];
        out.mkdirs();
        ram = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Memory mem = currentProgram.getMemory();
        boolean fresh = currentProgram.getFunctionManager().getFunctionCount() == 0;
        if (fresh) {
            setupSections(facts, mem);
            setupSyscalls(facts, mem);
            setupFunctions(facts);
            setupData(facts);
        } else {
            for (String[] r : tsv(new File(facts, "funcs.tsv"))) {
                funcNames.put(hex(r[0]), clean(r[3]));
                if (r[2].equals("1")) noret.add(hex(r[0]));
            }
        }
        for (String e : args[3].split(",")) {
            Function f = getFunctionAt(A(hex(e)));
            if (f == null) { printerr("no function at " + e); continue; }
            export(f, out, tag);
        }
    }

    static String clean(String n) {
        String s = n.replace(' ', '_');
        return s.length() > 200 ? s.substring(0, 200) : s;
    }

    void setupSections(File facts, Memory mem) throws Exception {
        for (String[] r : tsv(new File(facts, "sections.tsv"))) {
            String name = r[0];
            long lo = hex(r[1]), size = hex(r[2]), fl = hex(r[3]);
            if (size == 0) continue;
            MemoryBlock b = mem.getBlock(A(lo));
            if (b == null) continue;
            if (!b.getStart().equals(A(lo))) { mem.split(b, A(lo)); b = mem.getBlock(A(lo)); }
            if (b.getEnd().getOffset() > lo + size - 1) { mem.split(b, A(lo + size)); b = mem.getBlock(A(lo)); }
            b.setName(name);
            boolean x = (fl & 4) != 0, w = (fl & 1) != 0;
            b.setPermissions(true, w, x);
        }
    }

    static final String[][] SYSCALLS = {
        // name, return, params (type:name ...), noreturn
        {"abort", "void", "", "1"},
        {"sol_log_", "void", "char*:msg ulonglong:len", "0"},
        {"sol_log_data", "void", "void*:slices ulonglong:n", "0"},
        {"sol_log_pubkey", "void", "byte*:pubkey", "0"},
        {"sol_memcpy_", "void", "void*:dst void*:src ulonglong:n", "0"},
        {"sol_memmove_", "void", "void*:dst void*:src ulonglong:n", "0"},
        {"sol_memset_", "void", "void*:dst byte:c ulonglong:n", "0"},
        {"sol_memcmp_", "void", "void*:a void*:b ulonglong:n int*:result", "0"},
        {"sol_invoke_signed_rust", "ulonglong", "void*:instruction void*:account_infos ulonglong:n_infos void*:signers_seeds ulonglong:n_signers", "0"},
        {"sol_try_find_program_address", "ulonglong", "void*:seeds ulonglong:n_seeds byte*:program_id byte*:out_address byte*:out_bump", "0"},
        {"sol_create_program_address", "ulonglong", "void*:seeds ulonglong:n_seeds byte*:program_id byte*:out_address", "0"},
        {"sol_get_clock_sysvar", "ulonglong", "void*:out", "0"},
        {"sol_get_rent_sysvar", "ulonglong", "void*:out", "0"},
        {"sol_set_return_data", "void", "byte*:data ulonglong:len", "0"},
        {"sol_get_return_data", "ulonglong", "byte*:data ulonglong:len byte*:program_id", "0"},
        {"sol_sha256", "ulonglong", "void*:vals ulonglong:n byte*:out", "0"},
    };

    DataType dt(String t) {
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        switch (t) {
            case "void": return VoidDataType.dataType;
            case "ulonglong": return UnsignedLongLongDataType.dataType;
            case "byte": return ByteDataType.dataType;
            case "char*": return new PointerDataType(CharDataType.dataType, dtm);
            case "byte*": return new PointerDataType(ByteDataType.dataType, dtm);
            case "int*": return new PointerDataType(IntegerDataType.dataType, dtm);
            default: return new PointerDataType(VoidDataType.dataType, dtm);
        }
    }

    Map<String, Address> stubs = new HashMap<>();

    void setupSyscalls(File facts, Memory mem) throws Exception {
        long base = 0x200000000L;
        MemoryBlock b = mem.createInitializedBlock("sbf_syscalls", A(base), 8L * SYSCALLS.length, (byte) 0, monitor, false);
        b.setPermissions(true, false, true);
        for (int i = 0; i < SYSCALLS.length; i++) {
            String[] s = SYSCALLS[i];
            Address a = A(base + 8L * i);
            mem.setBytes(a, new byte[] {(byte) 0x95, 0, 0, 0, 0, 0, 0, 0});
            disassemble(a);
            Function f = createFunction(a, s[0]);
            FunctionDefinitionDataType fd = new FunctionDefinitionDataType(s[0]);
            fd.setReturnType(dt(s[1]));
            List<ParameterDefinition> ps = new ArrayList<>();
            for (String p : s[2].trim().split(" ")) {
                if (p.isEmpty()) continue;
                String[] tp = p.split(":");
                ps.add(new ParameterDefinitionImpl(tp[1], dt(tp[0]), null));
            }
            fd.setArguments(ps.toArray(new ParameterDefinition[0]));
            fd.setNoReturn(s[3].equals("1"));
            new ApplyFunctionSignatureCmd(a, fd, SourceType.USER_DEFINED).applyTo(currentProgram);
            if (s[3].equals("1")) f.setNoReturn(true);
            stubs.put(s[0], a);
        }
        ReferenceManager rm = currentProgram.getReferenceManager();
        int n = 0;
        // syscall sites are fixed after disassembly in setupFunctions (instructions must exist first)
        syscallSites = tsv(new File(facts, "syscalls.tsv"));
    }

    List<String[]> syscallSites;

    void setupFunctions(File facts) throws Exception {
        List<String[]> rows = tsv(new File(facts, "funcs.tsv"));
        AddressSet all = new AddressSet();
        for (String[] r : rows) {
            long a = hex(r[0]), size = hex(r[1]);
            all.add(A(a), A(a + size - 1));
            funcNames.put(a, clean(r[3]));
            if (r[2].equals("1")) noret.add(a);
        }
        // SBF .text has no inline data: disassemble every function body from its entry, restricted to the body
        for (String[] r : rows) {
            long a = hex(r[0]), size = hex(r[1]);
            DisassembleCommand cmd = new DisassembleCommand(A(a), new AddressSet(A(a), A(a + size - 1)), true);
            cmd.applyTo(currentProgram, monitor);
        }
        // any byte range left undecoded inside a body (unreachable code) is decoded linearly
        DisassembleCommand rest = new DisassembleCommand(all, all, false);
        rest.applyTo(currentProgram, monitor);
        FunctionManager fm = currentProgram.getFunctionManager();
        for (String[] r : rows) {
            long a = hex(r[0]), size = hex(r[1]);
            AddressSet body = new AddressSet(A(a), A(a + size - 1));
            Function f = fm.getFunctionAt(A(a));
            if (f == null) {
                try {
                    f = fm.createFunction(clean(r[3]), A(a), body, SourceType.IMPORTED);
                } catch (Exception e) {
                    printerr("createFunction " + r[0] + " " + e);
                    continue;
                }
            }
            if (noret.contains(a)) f.setNoReturn(true);
        }
        // syscall sites: replace the self-call that `call -1` decodes to
        ReferenceManager rm = currentProgram.getReferenceManager();
        for (String[] r : syscallSites) {
            Address site = A(hex(r[0]));
            Address stub = stubs.get(r[1]);
            if (stub == null && r.length > 2 && hex(r[2]) != 0) stub = A(hex(r[2]));
            if (stub == null) { printerr("unknown syscall " + r[1]); continue; }
            Instruction ins = getInstructionAt(site);
            if (ins == null) continue;
            rm.removeAllReferencesFrom(site);
            Reference ref = rm.addMemoryReference(site, stub, RefType.CALL_OVERRIDE_UNCONDITIONAL, SourceType.USER_DEFINED, 0);
            rm.setPrimary(ref, true);
            if (r[1].equals("abort") || noret.contains(stub.getOffset())) ins.setFallThrough(null);
            setEOLComment(site, "syscall " + r[1]);
        }
        // calls to noreturn functions have no fall-through
        InstructionIterator it = currentProgram.getListing().getInstructions(all, true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            if (!ins.getFlowType().isCall()) continue;
            for (Address t : ins.getFlows()) {
                if (noret.contains(t.getOffset())) { ins.setFallThrough(null); break; }
            }
        }
    }

    void setupData(File facts) throws Exception {
        Listing L = currentProgram.getListing();
        SymbolTable st = currentProgram.getSymbolTable();
        for (String[] r : tsv(new File(facts, "data.tsv"))) {
            long a = hex(r[0]);
            int n = Integer.parseInt(r[1]);
            String kind = r[2], lab = r[3];
            try {
                st.createLabel(A(a), lab, SourceType.IMPORTED).setPrimary();
                labels.put(a, lab);
                if (n <= 0) continue;
                L.clearCodeUnits(A(a), A(a + n - 1), false);
                if (kind.startsWith("str")) {
                    L.createData(A(a), new StringDataType(), n);
                } else if (kind.equals("u32")) {
                    L.createData(A(a), UnsignedIntegerDataType.dataType);
                } else if (kind.startsWith("pubkey") || (kind.startsWith("bytes") && n == 32)) {
                    L.createData(A(a), new ArrayDataType(ByteDataType.dataType, n, 1));
                }
            } catch (Exception e) {
                // overlapping objects: keep the first
            }
        }
        ReferenceManager rm = currentProgram.getReferenceManager();
        for (String[] r : tsv(new File(facts, "lddw.tsv"))) {
            Address site = A(hex(r[0]));
            long tgt = hex(r[1]);
            if (getInstructionAt(site) == null) continue;
            rm.addMemoryReference(site, A(tgt), RefType.DATA, SourceType.USER_DEFINED, 1);
            if (r.length > 3 && !r[3].isEmpty()) setEOLComment(site, r[3]);
        }
    }

    // ---------------------------------------------------------------- export

    String fname(Address a) {
        if (a == null) return "?";
        Function f = getFunctionAt(a);
        if (f != null) return f.getName();
        Symbol s = getSymbolAt(a);
        return s != null ? s.getName() : a.toString();
    }

    String calleeOf(Instruction ins) {
        for (Reference r : ins.getReferencesFrom()) {
            if (r.getReferenceType().isCall()) return fname(r.getToAddress());
        }
        Address[] fl = ins.getFlows();
        return fl.length > 0 ? fname(fl[0]) : "?";
    }

    static String js(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c == '\n') b.append("\\n");
            else if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
            else b.append(c);
        }
        return b.append('"').toString();
    }

    void export(Function f, File out, String tag) throws Exception {
        String stem = tag + "_" + Long.toHexString(f.getEntryPoint().getOffset());
        long base = f.getEntryPoint().getOffset();
        Listing L = currentProgram.getListing();
        // 1. listing with names
        try (PrintWriter w = new PrintWriter(new File(out, stem + ".lst"))) {
            w.println("// " + f.getName() + " @ " + f.getEntryPoint() + " body " + f.getBody().getNumAddresses() + " B");
            for (Instruction ins : L.getInstructions(f.getBody(), true)) {
                String extra = "";
                if (ins.getFlowType().isCall()) extra = "  ; -> " + calleeOf(ins);
                String c = ins.getComment(CommentType.EOL);
                if (c != null) extra += "  ; " + c;
                w.printf("%06x +%05x  %-40s%s%n", ins.getAddress().getOffset(), ins.getAddress().getOffset() - base,
                        ins.toString(), extra);
            }
        }
        // 2. CFG from instructions (leaders: entry, branch targets, after branches/exit/noreturn calls)
        TreeSet<Long> leaders = new TreeSet<>();
        leaders.add(base);
        List<Instruction> insl = new ArrayList<>();
        for (Instruction ins : L.getInstructions(f.getBody(), true)) insl.add(ins);
        for (Instruction ins : insl) {
            FlowType ft = ins.getFlowType();
            boolean ends = ft.isJump() || ft.isTerminal() || ins.getFallThrough() == null;
            if (ft.isJump()) for (Address t : ins.getFlows()) leaders.add(t.getOffset());
            if (ends) leaders.add(ins.getAddress().getOffset() + ins.getLength());
        }
        StringBuilder cfg = new StringBuilder("{\"function\":" + js(f.getName()) + ",\"entry\":" + base + ",\"blocks\":[\n");
        StringBuilder dot = new StringBuilder("digraph \"" + stem + "\" {\n node [shape=box,fontname=monospace,fontsize=9];\n");
        int i = 0, nb = 0;
        while (i < insl.size()) {
            Instruction first = insl.get(i);
            long start = first.getAddress().getOffset();
            List<String> calls = new ArrayList<>();
            int count = 0;
            Instruction last = first;
            while (i < insl.size()) {
                Instruction ins = insl.get(i);
                if (count > 0 && leaders.contains(ins.getAddress().getOffset())) break;
                last = ins; count++; i++;
                if (ins.getFlowType().isCall()) calls.add(calleeOf(ins));
                FlowType ft = ins.getFlowType();
                if (ft.isJump() || ft.isTerminal() || ins.getFallThrough() == null) break;
            }
            List<String> succ = new ArrayList<>();
            FlowType ft = last.getFlowType();
            long endNext = last.getAddress().getOffset() + last.getLength();
            if (ft.isJump()) for (Address t : last.getFlows())
                succ.add("{\"to\":" + (t.getOffset() - base) + ",\"kind\":\"" + (ft.isConditional() ? "taken" : "jump") + "\"}");
            if (last.getFallThrough() != null && !(ft.isJump() && !ft.isConditional()))
                succ.add("{\"to\":" + (endNext - base) + ",\"kind\":\"fall\"}");
            String term = ft.isTerminal() ? "exit" : (last.getFallThrough() == null && ft.isCall() ? "noreturn:" + calleeOf(last) : "");
            if (nb++ > 0) cfg.append(",\n");
            StringBuilder cl = new StringBuilder("[");
            for (int k = 0; k < calls.size(); k++) cl.append(k > 0 ? "," : "").append(js(calls.get(k)));
            cl.append("]");
            cfg.append("{\"off\":" + (start - base) + ",\"addr\":\"0x" + Long.toHexString(start) + "\",\"end\":" + (endNext - base)
                    + ",\"insns\":" + count + ",\"term\":" + js(term) + ",\"calls\":" + cl + ",\"succ\":[" + String.join(",", succ) + "]}");
            String lbl = String.format("+%x (%d)", start - base, count);
            for (String c : calls) {
                String s = c.length() > 48 ? c.substring(c.length() - 48) : c;
                lbl += "\\n" + s.replace("\"", "'");
            }
            if (!term.isEmpty()) lbl += "\\n[" + (term.length() > 40 ? term.substring(0, 40) : term).replace("\"", "'") + "]";
            dot.append(String.format(" b%x [label=\"%s\"];%n", start - base, lbl));
            if (ft.isJump()) for (Address t : last.getFlows())
                dot.append(String.format(" b%x -> b%x%s;%n", start - base, t.getOffset() - base, ft.isConditional() ? " [color=blue]" : ""));
            if (last.getFallThrough() != null && !(ft.isJump() && !ft.isConditional()))
                dot.append(String.format(" b%x -> b%x [style=dashed];%n", start - base, endNext - base));
        }
        cfg.append("\n]}\n");
        dot.append("}\n");
        Files.writeString(new File(out, stem + ".cfg.json").toPath(), cfg.toString());
        Files.writeString(new File(out, stem + ".cfg.dot").toPath(), dot.toString());

        // 3. decompile
        DecompInterface ifc = new DecompInterface();
        DecompileOptions opts = new DecompileOptions();
        opts.grabFromProgram(currentProgram);
        opts.setMaxPayloadMBytes(512);
        opts.setMaxInstructions(200000);
        ifc.setOptions(opts);
        ifc.toggleCCode(true);
        ifc.toggleSyntaxTree(true);
        ifc.setSimplificationStyle("decompile");
        ifc.openProgram(currentProgram);
        DecompileResults res = ifc.decompileFunction(f, 1800, monitor);
        if (!res.decompileCompleted()) {
            printerr("decompile failed " + f.getName() + ": " + res.getErrorMessage());
            Files.writeString(new File(out, stem + ".c").toPath(), "// decompile failed: " + res.getErrorMessage() + "\n");
            return;
        }
        Files.writeString(new File(out, stem + ".c").toPath(), res.getDecompiledFunction().getC());
        // address-annotated C: each line prefixed by the lowest window offset of its tokens
        ClangTokenGroup markup = res.getCCodeMarkup();
        StringBuilder ac = new StringBuilder();
        for (ClangLine line : DecompilerUtils.toLines(markup)) {
            long lo = Long.MAX_VALUE, hi = -1;
            StringBuilder t = new StringBuilder();
            for (ClangToken tok : line.getAllTokens()) {
                t.append(tok.getText());
                Address mn = tok.getMinAddress(), mx = tok.getMaxAddress();
                if (mn != null && mn.getAddressSpace() == ram && f.getBody().contains(mn)) lo = Math.min(lo, mn.getOffset());
                if (mx != null && mx.getAddressSpace() == ram && f.getBody().contains(mx)) hi = Math.max(hi, mx.getOffset());
            }
            String pre = lo == Long.MAX_VALUE ? "              " : String.format("/*%5x-%5x*/", lo - base, hi - base);
            ac.append(pre).append(" ".repeat(Math.max(0, line.getIndent()))).append(t).append('\n');
        }
        Files.writeString(new File(out, stem + ".addr.c").toPath(), ac.toString());
        // 4. frame map: decompiler stack symbols + raw r10 accesses
        HighFunction hf = res.getHighFunction();
        StringBuilder fm = new StringBuilder("{\"function\":" + js(f.getName()) + ",\"high_symbols\":[\n");
        int ns = 0;
        Iterator<HighSymbol> hs = hf.getLocalSymbolMap().getSymbols();
        List<HighSymbol> syms = new ArrayList<>();
        while (hs.hasNext()) syms.add(hs.next());
        for (HighSymbol s : syms) {
            VariableStorage vs = s.getStorage();
            String where = vs == null ? "?" : vs.toString();
            Long so = (vs != null && vs.isStackStorage()) ? (long) vs.getStackOffset() : null;
            if (ns++ > 0) fm.append(",\n");
            fm.append("{\"name\":" + js(s.getName()) + ",\"type\":" + js(s.getDataType().getDisplayName()) + ",\"size\":" + s.getSize()
                    + ",\"storage\":" + js(where) + (so != null ? ",\"r10_off\":" + so : "") + ",\"param\":" + s.isParameter() + "}");
        }
        fm.append("\n]}\n");
        Files.writeString(new File(out, stem + ".frame_ghidra.json").toPath(), fm.toString());
        // 5. ordered call list with the decompiler's statement text
        Map<String, String> stmtOf = new HashMap<>();
        List<ClangNode> toks = new ArrayList<>();
        markup.flatten(toks);
        for (ClangNode node : toks) {
            if (!(node instanceof ClangFuncNameToken)) continue;
            ClangFuncNameToken tok = (ClangFuncNameToken) node;
            PcodeOp op = tok.getPcodeOp();
            if (op == null) continue;
            ClangNode p = tok.Parent();
            while (p != null && !(p instanceof ClangStatement)) p = p.Parent();
            String text = p == null ? tok.getText() : p.toString().trim().replaceAll("\\s+", " ");
            stmtOf.put(op.getSeqnum().getTarget().toString() + "/" + op.getSeqnum().getTime(), text);
        }
        StringBuilder calls = new StringBuilder("{\"function\":" + js(f.getName()) + ",\"calls\":[\n");
        int nc = 0;
        for (Instruction ins : insl) {
            if (!ins.getFlowType().isCall()) continue;
            String callee = calleeOf(ins);
            String text = "";
            Iterator<PcodeOpAST> ops = hf.getPcodeOps(ins.getAddress());
            while (ops.hasNext()) {
                PcodeOpAST op = ops.next();
                if (op.getOpcode() == PcodeOp.CALL || op.getOpcode() == PcodeOp.CALLIND) {
                    String k = op.getSeqnum().getTarget().toString() + "/" + op.getSeqnum().getTime();
                    if (stmtOf.containsKey(k)) text = stmtOf.get(k);
                    else {
                        StringBuilder a = new StringBuilder(callee + "(");
                        for (int j = 1; j < op.getNumInputs(); j++) {
                            Varnode v = op.getInput(j);
                            HighVariable h = v.getHigh();
                            a.append(j > 1 ? ", " : "").append(v.isConstant() ? "0x" + Long.toHexString(v.getOffset()) : h != null && h.getName() != null ? h.getName() : v.toString());
                        }
                        text = a.append(")").toString();
                    }
                }
            }
            if (nc++ > 0) calls.append(",\n");
            calls.append("{\"off\":" + (ins.getAddress().getOffset() - base) + ",\"callee\":" + js(callee) + ",\"noreturn\":" + (ins.getFallThrough() == null)
                    + ",\"c\":" + js(text) + "}");
        }
        calls.append("\n]}\n");
        Files.writeString(new File(out, stem + ".calls.json").toPath(), calls.toString());
        ifc.dispose();
        println("exported " + stem + " " + f.getName());
    }
}
