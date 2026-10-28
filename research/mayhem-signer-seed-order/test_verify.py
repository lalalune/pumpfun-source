"""Counterexamples against actual retained artifacts and source bindings."""
from pathlib import Path
import gzip,importlib.util,io,json,shutil,struct,tarfile,tempfile,unittest
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cpi_order_test_verifier',HERE/'verify.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cpi-order-test-');self.root=Path(self.tmp.name)/'packet';shutil.copytree(HERE,self.root)
    def tearDown(self):self.tmp.cleanup()
    def save(self,p,obj):p.write_bytes(gzip.compress((json.dumps(obj,indent=2)+'\n').encode(),mtime=0) if p.suffix=='.gz' else (json.dumps(obj,indent=2)+'\n').encode())
    def elf(self,label='late-inline'):
        spec=importlib.util.spec_from_file_location('test_retained_reader',HERE/'reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        p=Path(self.tmp.name)/'input.so';p.write_bytes(v.raw(self.root/'builds'/label/'symbols.so.gz'));return reader.Elf(p)
    def test_complete_relocated_replay(self):self.assertEqual(v.verify(self.root),v.read(self.root/'report.json'))
    def test_context_byte_offset(self):
        e=self.elf();w=v.handler(e);at=w['start']+v.bump_read(e,w)['offset'];b=bytearray(e.b);struct.pack_into('<h',b,at+2,0x23);e.b=bytes(b)
        with self.assertRaisesRegex(ValueError,'byte-load'):v.bump_read(e,w)
    def test_context_register_origin(self):
        e=self.elf();w=v.handler(e);at=w['start']+v.bump_read(e,w)['offset'];b=bytearray(e.b);b[at+1]=1;e.b=bytes(b)
        with self.assertRaisesRegex(ValueError,'spill chain'):v.bump_read(e,w)
    def test_spill_link(self):
        e=self.elf();w=v.handler(e);chain=v.bump_read(e,w)['syntactic_argument_spill_chain'];at=w['start']+chain[-1]['offset'];b=bytearray(e.b);struct.pack_into('<h',b,at+2,-4096);e.b=bytes(b)
        with self.assertRaisesRegex(ValueError,'spill chain'):v.bump_read(e,w)
    def test_masked_direct_target(self):
        e=self.elf();w=v.handler(e);at=w['direct'][0]['pc'];b=bytearray(e.b);struct.pack_into('<i',b,at+4,0);e.b=bytes(b);changed=e.window(w['start'],w['end'])
        self.assertEqual(v.shape(changed),v.shape(w))
        with self.assertRaisesRegex(ValueError,'complete window'):v.call_shapes(changed,v.functions(e))
    def test_source_outside_handler(self):
        p=self.root/'source/late-inline.rs';p.write_bytes(p.read_bytes().replace(b'pub struct SellEvent',b'pub struct OtherEvent',1))
        with self.assertRaisesRegex(ValueError,'source binding'):v.verify(self.root,False)
    def test_extra_file(self):
        (self.root/'unlisted.txt').write_text('unlisted',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'manifest'):v.manifest_check(self.root)
    def test_missing_failed_evidence(self):
        (self.root/'failed/temporary-signers/stderr.log.gz').unlink()
        with self.assertRaisesRegex(ValueError,'manifest'):v.manifest_check(self.root)
    def test_failed_build_status(self):
        p=self.root/'builds/late-inline/result.json.gz';r=v.read(p);r['status']='FAILED';self.save(p,r)
        with self.assertRaisesRegex(ValueError,'failed/unexecuted'):v.verify(self.root,False)
    def test_nonallocated_whole_repeat_difference(self):
        p=self.root/'builds/baseline-repeat/symbols.so.gz';b=v.raw(p)+b'\0';p.write_bytes(gzip.compress(b,mtime=0));pin=v.identity(b)
        r=self.root/'builds/baseline-repeat/result.json.gz';x=v.read(r);x['outputs']['symbols.so']=pin;self.save(r,x)
        r=self.root/'builds.json';x=v.read(r);x['baseline-repeat']['outputs']['symbols.so']=pin;self.save(r,x)
        with self.assertRaisesRegex(ValueError,'baseline root repeat'):v.verify(self.root,False)
    def test_archive_traversal(self):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as t:
            m=tarfile.TarInfo('../outside');m.size=1;t.addfile(m,io.BytesIO(b'x'))
        with self.assertRaisesRegex(ValueError,'unsafe archive'):v.unpack(buf.getvalue())

    def composition(self):
        spec=importlib.util.spec_from_file_location('test_composition',self.root/'composition/verify.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);return c
    def test_composition_source_transform(self):
        p=self.root/'composition/sources/price-eager-inline.rs';p.write_bytes(p.read_bytes().replace(b'let delta=scaled/10_000;',b'let delta=scaled/9_999;',1))
        c=self.composition();base=c.sources(self.root/'composition',v)
        with self.assertRaisesRegex(ValueError,'source transform'):c.variant(self.root/'composition',v,base,'price-eager-inline')
    def test_composition_masked_call_permutation(self):
        c=self.composition();spec=importlib.util.spec_from_file_location('composition_test_reader',HERE/'reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        p=Path(self.tmp.name)/'composition.so';p.write_bytes(v.raw(self.root/'composition/builds/baseline/symbols.so.gz'));e=reader.Elf(p)
        p=Path(self.tmp.name)/'original.so';p.write_bytes(v.raw(self.root/'reference/original.so.gz'));original=reader.Elf(p);originals={r['id']:original.window(r['start'],r['end']) for r in v.read(self.root/'reference/original-windows.json')}
        w,_=c.body(v,e,originals,'sell','O0082');before=c.measure(v,e,original,originals)['handlers']['O0082'];a,b=w['direct'][4:6];self.assertNotEqual(a['target'],b['target'])
        raw=bytearray(e.b)
        for call,target in [(a,b['target']),(b,a['target'])]:struct.pack_into('<i',raw,call['pc']+4,(target-call['pc']-8)//8)
        e.b=bytes(raw);after=c.measure(v,e,original,originals)['handlers']['O0082']
        self.assertEqual(v.shape(w),v.shape(e.window(w['start'],w['end'])))
        self.assertTrue(before['callee_multiset_equal'] and after['callee_multiset_equal'])
        self.assertNotEqual(before['ordered_matches'],after['ordered_matches'])
    def test_composition_missing_repeat(self):
        (self.root/'composition/builds/late-inline-repeat/symbols.so.gz').unlink()
        with self.assertRaisesRegex(ValueError,'manifest'):v.manifest_check(self.root)
    def test_composition_fresh_source_binding(self):
        p=self.root/'composition/rebuild-validation/launch.json.gz';r=v.read(p);r['source_inputs']['src/state.rs']='0'*64;self.save(p,r)
        with self.assertRaisesRegex(ValueError,'fresh composition source binding'):self.composition().verify(self.root/'composition',False)
    def placement(self):
        spec=importlib.util.spec_from_file_location('test_placement',self.root/'composition/placement/verify.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);return p
    def test_placement_changed_trace_call(self):
        p=self.placement();c=self.composition();spec=importlib.util.spec_from_file_location('placement_test_reader',HERE/'reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        folder=self.root/'composition/placement/builds/baseline-placement';f=Path(self.tmp.name)/'placement.so';f.write_bytes(v.raw(folder/'symbols.so.gz'));e=reader.Elf(f)
        f=Path(self.tmp.name)/'original.so';f.write_bytes(v.raw(self.root/'reference/original.so.gz'));o=reader.Elf(f);originals={r['id']:o.window(r['start'],r['end']) for r in v.read(self.root/'reference/original-windows.json')}
        log=v.raw(folder/'stderr.log.gz').decode();marker='# *** IR Dump After';a=log.index(marker);changed=log[:a]+log[a:].replace('JAL &__multi3,','JAL &__udivti3,',1);self.assertNotEqual(log,changed)
        with self.assertRaisesRegex(ValueError,'post-placement callees'):p.trace_analysis(v,c,e,originals,changed)
    def test_placement_prefix_only_allows_return_rename(self):
        p=self.placement();folder=self.root/'composition/placement/builds';a=p.handler_ir(v,v.raw(folder/'baseline-ir/module.ll.gz'))[0];b=p.handler_ir(v,v.raw(folder/'late-inline-ir/module.ll.gz'))[0]
        changed=b.replace('ptr %_189, i64 72','ptr %_189, i64 80',1);self.assertNotEqual(b,changed)
        with self.assertRaisesRegex(ValueError,'prefix differs beyond return labels'):p.compare_prefix(v,a,changed)
    def test_placement_rejects_false_unstripped_identity(self):
        f=self.root/'composition/placement/builds/baseline-ir/result.json.gz';r=v.read(f);r['complete_outputs_equal_parent']=True;self.save(f,r)
        with self.assertRaisesRegex(ValueError,'unstripped identity claim'):self.placement().verify(self.root/'composition/placement',False)

    def arithmetic(self):
        spec=importlib.util.spec_from_file_location('test_arithmetic',self.root/'composition/arithmetic/verify.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);return a
    def arithmetic_elf(self,label='overflow-late'):
        spec=importlib.util.spec_from_file_location('arithmetic_test_reader',HERE/'reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        f=Path(self.tmp.name)/'arithmetic.so';f.write_bytes(v.raw(self.root/'composition/arithmetic/builds'/label/'symbols.so.gz'));e=reader.Elf(f)
        f=Path(self.tmp.name)/'original.so';f.write_bytes(v.raw(self.root/'reference/original.so.gz'));o=reader.Elf(f);originals={r['id']:o.window(r['start'],r['end']) for r in v.read(self.root/'reference/original-windows.json')}
        c=self.composition();w=c.body(v,e,originals,'sell','O0082')[0];return e,w,originals,c
    def test_arithmetic_source_divisor(self):
        a=self.arithmetic();c=self.composition();p=self.root/'composition/arithmetic/sources/overflow-late.rs';b=p.read_bytes();changed=b.replace(b'else{scaled}/10_000;',b'else{scaled}/9_999;',1);self.assertNotEqual(b,changed);p.write_bytes(changed)
        with self.assertRaisesRegex(ValueError,'source transform'):a.variant(self.root/'composition/arithmetic',v,c,c.sources(self.root/'composition',v),'overflow-late')
    def test_arithmetic_guard_operand(self):
        a=self.arithmetic();e,w,originals,c=self.arithmetic_elf();raw=bytearray(e.b);raw[w['start']+560+1]=7;e.b=bytes(raw)
        with self.assertRaisesRegex(ValueError,'low-bit mask'):a.byte_witness(v,c,e,w,originals,'overflow-late')
    def test_arithmetic_guard_target(self):
        a=self.arithmetic();e,w,originals,c=self.arithmetic_elf();raw=bytearray(e.b);struct.pack_into('<h',raw,w['start']+568+2,44);e.b=bytes(raw)
        with self.assertRaisesRegex(ValueError,'guard branch'):a.byte_witness(v,c,e,w,originals,'overflow-late')
    def test_arithmetic_masked_price_target(self):
        a=self.arithmetic();e,w,originals,c=self.arithmetic_elf();raw=bytearray(e.b);call=next(x for x in w['direct'] if x['offset']==552);pc=w['start']+512;struct.pack_into('<i',raw,pc+4,(call['target']-pc-8)//8);e.b=bytes(raw);changed=e.window(w['start'],w['end']);self.assertEqual(v.shape(w),v.shape(changed))
        with self.assertRaisesRegex(ValueError,'price call target'):a.byte_witness(v,c,e,changed,originals,'overflow-late')
    def test_arithmetic_unrecognized_slot_index(self):
        import re
        a=self.arithmetic();e,_,_,_=self.arithmetic_elf('baseline-stages');log=v.raw(self.root/'composition/arithmetic/builds/baseline-stages/stderr.log.gz').decode('utf-8')
        changed,n=re.subn(r'(?m)^(\d+)B(\s+JAL\s)',r'\1Z\2',log,count=1);self.assertEqual(n,1)
        with self.assertRaisesRegex(ValueError,'unparsed arithmetic MIR call'):a.machine_trace(v,changed,'Before Machine Instruction Scheduler (machine-scheduler)',e)
    def test_arithmetic_nonallocated_repeat_byte(self):
        folder=self.root/'composition/arithmetic/builds/overflow-late-repeat';p=folder/'symbols.so.gz';b=v.raw(p)+b'\0';p.write_bytes(gzip.compress(b,mtime=0));r=v.read(folder/'result.json.gz');r['outputs']['symbols.so']=v.identity(b);self.save(folder/'result.json.gz',r)
        with self.assertRaisesRegex(ValueError,'complete repeat differs'):self.arithmetic().verify(self.root/'composition/arithmetic',False)
    def test_arithmetic_fresh_source_binding(self):
        p=self.root/'composition/arithmetic/rebuild-validation/launch.json.gz';r=v.read(p);r['source_inputs']['src/instructions/pump_interface.rs']='0'*64;self.save(p,r)
        with self.assertRaisesRegex(ValueError,'fresh source/tool binding'):self.arithmetic().verify(self.root/'composition/arithmetic',False)
    def guard(self):
        spec=importlib.util.spec_from_file_location('test_guard',self.root/'composition/arithmetic/guard/verify.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);return g
    def test_guard_source_order(self):
        g=self.guard();a=self.arithmetic();c=self.composition();p=self.root/'composition/arithmetic/guard/sources/checked-price-first-late.rs';b=p.read_bytes();old,new=g.TRANSFORMS['checked-price-first-late'];self.assertEqual(b.count(new),1);p.write_bytes(b.replace(new,old))
        with self.assertRaisesRegex(ValueError,'guard source transform'):g.variant(self.root/'composition/arithmetic/guard',v,c,a,c.sources(self.root/'composition',v),'checked-price-first-late')
    def test_guard_error_block_target(self):
        g=self.guard();c=self.composition();spec=importlib.util.spec_from_file_location('guard_test_reader',HERE/'reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
        p=Path(self.tmp.name)/'guard.so';p.write_bytes(v.raw(self.root/'composition/arithmetic/guard/builds/checked-price-first-late/symbols.so.gz'));e=reader.Elf(p)
        p=Path(self.tmp.name)/'original.so';p.write_bytes(v.raw(self.root/'reference/original.so.gz'));o=reader.Elf(p);originals={r['id']:o.window(r['start'],r['end']) for r in v.read(self.root/'reference/original-windows.json')};w=c.body(v,e,originals,'sell','O0082')[0]
        b=bytearray(e.b);struct.pack_into('<h',b,w['start']+960+2,7);e.b=bytes(b)
        with self.assertRaisesRegex(ValueError,'guard error jump'):g.witness(v,c,e,w,originals,'checked-price-first-late')
    def test_guard_ir_profile_evidence(self):
        g=self.guard();a=self.arithmetic();p=self.root/'composition/arithmetic/guard/builds/checked-price-first-late/stderr.log.gz';b=v.raw(p).decode('utf-8');fragment=a.ir_fragment(v,b,'CodeGen Prepare (codegenprepare)');observation=a.ir_order(v,fragment);lines=fragment.splitlines();guard=lines[observation['guard']-1];self.assertIn('!prof',guard);changed=b.replace(guard,guard.split(', !prof')[0],1);self.assertNotEqual(b,changed);p.write_bytes(gzip.compress(changed.encode(),mtime=0))
        with self.assertRaisesRegex(ValueError,'guard IR profile/position'):g.verify(self.root/'composition/arithmetic/guard',False)
    def test_guard_fresh_wrong_variant(self):
        p=self.root/'composition/arithmetic/guard/rebuild-validation/comparison.json.gz';r=v.read(p);r['variant']='option-projection-late';self.save(p,r)
        with self.assertRaisesRegex(ValueError,'guard fresh output/variant'):self.guard().verify(self.root/'composition/arithmetic/guard',False)

if __name__=='__main__':unittest.main()
