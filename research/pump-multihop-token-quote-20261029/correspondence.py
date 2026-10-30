"""Finite independently evaluated definitions, signed wires, prestates and receipt joins.
No import of executed producers, LiteSVM, or compiler. Host executable fingerprints
are retained pinned provenance; this portable verifier does not execute those files.
"""
if not __debug__:
    raise SystemExit("Run without -O")
import base64,hashlib,json,re,struct
from pathlib import PurePosixPath
from solders.pubkey import Pubkey
from solders.transaction import Transaction

def need(ok,message):
    if not ok:raise AssertionError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":")).encode()
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
AMM="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ATA="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
FEES="pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ"
WSOL="So11111111111111111111111111111111111111112"
PROGRAMS=[(AMM,"original/pump_amm"),(TOKEN,"dependencies/spl_token"),(TOKEN22,"dependencies/spl_token_2022"),(ATA,"dependencies/associated_token"),(FEES,"original/pump_fees")]

def definitions():
    regression=[dict(name="tokenkeg_sell_control",sell=True),dict(name="tokenkeg_buy_control",sell=False),dict(name="truncated_fee_config",sell=True,extension="truncated"),dict(name="short_tlv_header",sell=True,extension="short_header"),dict(name="no_extension_wrong_address",sell=True,extension="none"),dict(name="valid_zero_fee_wrong_address",sell=True,extension="valid"),dict(name="valid_fee_wrong_address",sell=True,extension="valid",bps=25),dict(name="native_quote_address_control",sell=False,native_wrong_address=True),dict(name="valid_fee_quote_owner_control",sell=True,extension="valid",correct_quote_address=True),dict(name="truncated_fee_before_quote_owner",sell=True,extension="truncated",correct_quote_address=True),dict(name="token2022_zero_fee_sell",sell=True,extension="valid",correct_quote_address=True,token2022_flow=True),dict(name="token2022_capped_fee_sell",sell=True,extension="valid",bps=25,correct_quote_address=True,token2022_flow=True),dict(name="token2022_capped_fee_buy",sell=False,extension="valid",bps=25,correct_quote_address=True,token2022_flow=True)]
    arithmetic=[dict(name="token2022_full_fee_small_buy",sell=False,extension="valid",bps=10000,correct_quote_address=True,token2022_flow=True,amount=3),dict(name="token2022_full_fee_ordinary_buy",sell=False,extension="valid",bps=10000,correct_quote_address=True,token2022_flow=True,amount=1000)]
    gate=[dict(name="token2022_uncapped_full_fee_zero_quote_buy",sell=False,extension="valid",bps=10000,maximum_fee=2**64-1,correct_quote_address=True,token2022_flow=True,amount=3)]
    return {"regression":regression,"arithmetic":arithmetic,"zeroquote":gate}

def key(value):return Pubkey.from_string(value)
def pda(seeds,program):return str(Pubkey.find_program_address(seeds,key(program))[0])
def addresses(case,fixture):
    keys=fixture["selected_outer_account_keys"];user=keys[0];a=keys[16];ca=keys[18];b=str(Pubkey.from_bytes(bytes([84])*32));cb=pda([b"bonding-curve",bytes(key(b))],PUMP)
    ata=lambda owner,mint,program=TOKEN:pda([bytes(key(owner)),bytes(key(program)),bytes(key(mint))],ATA)
    return dict(keys=keys,user=user,a=a,b=b,ca=ca,cb=cb,
        va=ata(ca,a,TOKEN22 if case.get("token2022_flow")else TOKEN),
        vqa=str(Pubkey.from_bytes(bytes([146])*32))if case.get("native_wrong_address")else ata(ca,WSOL),
        vb=ata(cb,b),vqb=ata(cb,a,TOKEN22 if case.get("correct_quote_address")else TOKEN),
        uw=ata(user,WSOL),ub=ata(user,b))

def expected_wire(case,fixture,idl):
    a=addresses(case,fixture);ix=next(i for i in idl["instructions"]if i["name"]=="multi_hop_swap")
    fixed=list(a["keys"][:16]);fixed[1]=a["ub"]if case["sell"]else a["uw"];fixed[2]=a["uw"]if case["sell"]else a["ub"]
    need(len(ix["accounts"])==16,"source IDL fixed account count")
    metas=[(k,bool(v.get("signer")),bool(v.get("writable")))for k,v in zip(fixed,ix["accounts"])]
    aa=[a["a"],WSOL,a["ca"],a["va"],a["vqa"]];bb=[a["b"],a["a"],a["cb"],a["vb"],a["vqb"]]
    for group in ([bb,aa]if case["sell"]else[aa,bb]):metas.extend((k,False,i>=2)for i,k in enumerate(group))
    payload=bytes(ix["discriminator"])+struct.pack("<QQ",case.get("amount",10**6),1)
    return a,metas,payload

def check_wire(result,observation,case,fixture,idl):
    a,metas,payload=expected_wire(case,fixture,idl)
    wire=base64.b64decode(result["transaction_base64"],validate=True);tx=Transaction.from_bytes(wire);msg=tx.message
    need(bytes(tx)==wire and len(tx.signatures)==1 and all(tx.verify_with_results()),"verified canonical signed wire")
    need(result["transaction_sha256"]==sha(wire)and result["verified_signature_count"]==1 and result["fresh_vm"]is True,"signed result identity")
    need(observation["transaction_base64"]==result["transaction_base64"]and observation["signatures_verified"]is True,"observer signed wire join")
    need(str(tx.signatures[0])==observation["metadata"]["signature"],"metadata signature join")
    need(len(msg.instructions)==1 and str(msg.account_keys[0])==a["user"],"fixture exact instruction count/payer")
    ix=msg.instructions[0]
    need(str(msg.account_keys[ix.program_id_index])==AMM and bytes(ix.data)==payload,"fixture signed operation/amount/limit")
    need([str(msg.account_keys[i])for i in ix.accounts]==[k for k,s,w in metas],"fixture signed account roles/order")
    effective={AMM:(False,False),a["user"]:(True,True)}
    for k,s,w in metas:
        os,ow=effective.get(k,(False,False));effective[k]=(s or os,w or ow)
    keys=list(map(str,msg.account_keys));need(len(set(keys))==len(keys)and set(keys)==set(effective),"fixture signed key membership")
    h=msg.header
    for i,k in enumerate(keys):
        signer=i<h.num_required_signatures;writable=i<h.num_required_signatures-h.num_readonly_signed_accounts if signer else i<len(keys)-h.num_readonly_unsigned_accounts
        need((signer,writable)==effective[k],"fixture signed effective privileges")
    return a,keys,metas

def account(raw,lamports,owner):return dict(lamports=lamports,owner=owner,data_hex=raw.hex())
def token(mint,owner,amount):
    raw=bytearray(165);raw[:32]=bytes(key(mint));raw[32:64]=bytes(key(owner));struct.pack_into("<Q",raw,64,amount);raw[108]=1;return bytes(raw)

def source_prestate(case,fixture,idl):
    a=addresses(case,fixture);keys=a["keys"]
    state={k:None if v is None else dict(lamports=v["lamports"],owner=v["owner"],data_hex=v["data_hex"])for k,v in fixture["accounts"].items()}
    # Observer overrides are applied at the exact fixture set_account points.
    if case.get("token2022_flow"):
        row=state[keys[19]];raw=bytes.fromhex(row["data_hex"])[:165]+b"\x02"+struct.pack("<HHQ",2,8,0);state[a["va"]]=account(raw,row["lamports"],TOKEN22)
    if case.get("native_wrong_address"):state[a["vqa"]]=dict(state[keys[20]])
    disc=next(v["discriminator"]for v in idl["accounts"]if v["name"]=="UserVolumeAccumulator")
    state[keys[5]]=account(bytes(disc)+bytes(key(a["user"]))+bytes(97),10**9,AMM)
    curve=bytearray.fromhex(state[a["ca"]]["data_hex"])
    need(len(curve)==166 and curve[48]==0 and curve[81:83]==b"\0\0"and curve[83:115]==bytes(32)and curve[124]==0,"source curve template")
    for off in [8,16,24,32,40,142]:struct.pack_into("<Q",curve,off,10**15)
    curve[83:115]=bytes(key(a["a"]));curve[125:141]=bytes(16);curve[141]=1;state[a["cb"]]=account(curve,10**9,PUMP)
    mint=state[a["a"]];state[a["b"]]=account(bytes.fromhex(mint["data_hex"]),mint["lamports"],TOKEN)
    state[a["vb"]]=account(token(a["b"],a["cb"],10**15),10**9,TOKEN)
    state[a["vqb"]]=account(token(a["a"],a["cb"],10**15),10**9,TOKEN)
    if case.get("extension"):
        if case.get("token2022_flow"):
            raw=bytes.fromhex(state[a["vqb"]]["data_hex"])[:165]+b"\x02"+struct.pack("<HHQ",2,8,0);state[a["vqb"]]=account(raw,10**9,TOKEN22)
        payload=bytes(72)+struct.pack("<QQH",0,100,case.get("bps",0))*2
        ext=case["extension"];tlv=struct.pack("<HH",1,108)+(payload if ext=="valid"else b"")if ext!="none"else b""
        if ext=="short_header":tlv=b"\x01"
        raw=bytearray(bytes.fromhex(mint["data_hex"])[:82]+bytes(83)+b"\x01"+tlv)
        if "maximum_fee"in case:
            need(len(raw)==278 and struct.unpack_from("<HH",raw,166)==(1,108),"maximum-fee declared extension")
            for off in [250,268]:struct.pack_into("<Q",raw,off,case["maximum_fee"])
        state[a["a"]]=account(raw,mint["lamports"],TOKEN22)
    state[a["ub"]]=account(token(a["b"],a["user"],10**15),10**9,TOKEN)
    old=state[keys[1]];state[a["uw"]]=account(bytes.fromhex(old["data_hex"]),old["lamports"],TOKEN)
    old=state[keys[14]];raw=bytes.fromhex(old["data_hex"])
    fee=(raw[:41]+struct.pack("<QQQ",0,70,25)+struct.pack("<I",1)+bytes(16)+struct.pack("<QQQ",0,60,30)+struct.pack("<I",0)+struct.pack("<QQQ",0,80,40)).ljust(4097,b"\0")
    state[keys[14]]=account(fee,old["lamports"],old["owner"])
    return state

def prestate(result,observation,case,fixture,idl,keys,metas):
    state=source_prestate(case,fixture,idl);observed=observation["before"]
    need([v["key"]for v in observed]==keys,"observer exact signed key order")
    rows={v["key"]:v for v in observed}
    watched={k for k,s,w in metas if not rows[k].get("executable",False)}
    need(set(result["before"])==watched==set(result["after"]),"watched source account membership")
    for k in watched:
        expected=state.get(k)
        need(result["before"][k]==expected,"source-owned complete prestate")
        if expected is None:need(rows[k]==dict(key=k,missing=True),"source missing prestate")
        else:
            raw=bytes.fromhex(expected["data_hex"])
            need(rows[k]==dict(key=k,owner=expected["owner"],lamports=expected["lamports"],data_sha256=sha(raw),executable=False),"source-owned observer metadata/hash")
    # The observer does not retain an independent post-state hash snapshot. The
    # complete returned post-state is compared across all three actual reports.

METER=re.compile(r"^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$")
def logs(result):return [x for x in result["logs"]if not METER.fullmatch(x)]

def outputs_and_inputs(packet,repo,images,read,doc):
    mapping_raw=(packet/"runtime/input-map.json").read_bytes()
    need(sha(mapping_raw)=="7e90ba3dd9042e9e12cbc7d63eb20b11c6c4b3736be380a460a0e2c6e48f807b","reviewed complete runtime input map")
    mapping=json.loads(mapping_raw);host=[];checked=outputs=0
    commands={"standard":"6b4d3e383be631c73a8c224add8f730653768d6d6e311d648fc82051f2c2c53a","upstream-gate":"945a49a136095bb0432fd287017b1770046f8c8e6c6e572e64c376167aed6e54"}
    for family,names,count in [("standard",["arithmetic","regression"],38),("upstream-gate",["zeroquote"],39)]:
        folder=packet/"runtime"/family;e=doc(folder/"execution.json")
        need([x["name"]for x in e["results"]]==names and all(x["returncode"]==0 for x in e["results"]),"exact runtime result names/success")
        need(sha(canonical(e["commands"]))==commands[family],"exact runtime commands")
        rows=[x for x in mapping if x["receipt"]==family]
        need(len(rows)==count==len(e["inputs"]) and {r["actual_path"]for r in rows}==set(e["inputs"])==set(e["inputs_unchanged"])and all(x is True for x in e["inputs_unchanged"].values()),"exact runtime input membership/preservation")
        for row in rows:
            expected={k:row[k]for k in ["sha256","bytes"]};need(e["inputs"][row["actual_path"]]==expected,"runtime source input receipt")
            if row["kind"]=="host-runtime":host.append(expected);continue
            path=PurePosixPath(row["path"]);need(not path.is_absolute()and ".."not in path.parts,"safe mapped input")
            root=packet if row["kind"]=="packet"else repo
            need(row["kind"]in["packet","repo"],"known input mapping kind")
            raw=read(root/row["path"]);need(dict(sha256=sha(raw),bytes=len(raw))==expected,"actual runtime input bytes");checked+=1
        report_names=["arithmetic-two.json.gz","regression-thirteen.json.gz"]if family=="standard"else["zeroquote-one.json.gz"]
        expected_outputs=set(report_names)|{n+"."+kind+".log"for n in names for kind in["stdout","stderr"]}
        need(set(e["output_files"])==expected_outputs,"exact runtime output membership")
        need({p.name for p in folder.iterdir()if p.is_file()}==expected_outputs|{"execution.json"},"runtime directory membership")
        for name in expected_outputs:
            raw=(folder/name).read_bytes();need(e["output_files"][name]==dict(sha256=sha(raw),bytes=len(raw)),"actual runtime output receipt join");outputs+=1
        for result in e["results"]:
            for kind in ["stdout","stderr"]:need(result[kind+"_sha256"]==e["output_files"][result["name"]+"."+kind+".log"]["sha256"],"runtime result stream receipt join")
    need(checked==73 and len(host)==4 and outputs==9,"finite receipt totals")
    return dict(input_records=77,packet_or_repository_byte_joins=73,pinned_host_fingerprints=4,output_files=9,execution_receipts=2)

def verify(packet,repo,images,read,doc):
    receipt_report=outputs_and_inputs(packet,repo,images,read,doc)
    fixture_raw=(packet/"runtime/inputs/base-fixture.json").read_bytes();original_fixture=(packet/"runtime/inputs/upstream/runtime/inputs/base-fixture.json").read_bytes()
    need(sha(original_fixture)=="0f269b3e5766fc77fd493d41f68d31ad1b3fd865ac977709d6ba552a192e448f","source-owned original fixture")
    need((repo/"research/pump-multi-hop-quote-admission/runtime/inputs/base-fixture.json").read_bytes()==original_fixture,"repository fixture agrees")
    need(fixture_raw.replace(b"\r\n",b"\n")==original_fixture,"executed fixture newline-only transform")
    fixture=json.loads(fixture_raw);idl=doc(repo/"evidence/upstream/pump_amm.json")
    expected=definitions();original=(repo/"evidence/original/pump/deployed.so").read_bytes()
    raw={"original":original,"parent":images["parent"]["candidate"],"proposal":images["candidate"]["candidate"]};hashes={k:sha(v)for k,v in raw.items()}
    capture=doc(repo/"evidence/original/pump/capture.json");program=(repo/"evidence/original/pump/program-account.bin").read_bytes();pd=(repo/"evidence/original/pump/programdata-account.bin").read_bytes();header=pd[:45]
    need(sha(original)=="7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"and pd[45:]==original and sha(pd)==capture["programdata_sha256"]and sha(original)==capture["payload_sha256"]and len(original)==capture["payload_bytes"],"captured allocation/payload join")
    need(len(program)==36 and program[4:]==bytes(key(capture["programdata"])) ,"captured Program account")
    load_receipts={}
    for label,value in raw.items():
        need(len(value)<=len(original),"ELF allocation bound");allocated=header+value+bytes(len(original)-len(value))
        load_receipts[label]=dict(elf_sha256=sha(value),elf_bytes=len(value),program_owner=capture["owner"],program_bytes=len(program),program_sha256=sha(program),programdata_bytes=len(allocated),programdata_sha256=sha(allocated),header_sha256=sha(header),elf_prefix_unchanged=True,zero_allocation_tail=True,slot=struct.unpack_from("<Q",header,4)[0]+1)
    dependency_hashes={pid:sha((repo/"evidence"/path/"deployed.so").read_bytes())for pid,path in PROGRAMS}
    expected_errors=[None,None,"6063","2006","InvalidAccountData","2006","2006","2006","6010","6063",None,None,None]
    outcomes=[];signed=loads=successes=0
    families=[("regression","standard/regression-thirteen.json.gz","inputs/focused.py"),("arithmetic","standard/arithmetic-two.json.gz","inputs/focused_arithmetic.py"),("zeroquote","upstream-gate/zeroquote-one.json.gz","zeroquote-inputs/focused_zero_quote.py")]
    for family,file,producer in families:
        report=doc(packet/"runtime"/file)
        need(report["images_sha256"]==hashes,"report actual image identities")
        need(report["producer_sha256"]==sha((packet/"runtime"/producer).read_bytes())and report["fixture_sha256"]==sha((packet/"runtime/inputs/pump_tokenkeg_two_curve_differential.py").read_bytes()),"actual producer/fixture script")
        need([row["case"]for row in report["cases"]]==expected[family],"exact source-owned "+family+" definitions")
        for i,row in enumerate(report["cases"]):
            case=row["case"];runs=row["runs"];observations=row["observations"]
            need(set(runs)==set(observations)==set(raw),"three actual role membership")
            for label,result in runs.items():
                observation=observations[label];a,keys,metas=check_wire(result,observation,case,fixture,idl);signed+=1
                prestate(result,observation,case,fixture,idl,keys,metas)
                meta=observation["metadata"]
                need(meta["logs"]==result["logs"]and meta["inner_instructions"]==result["inner"]and meta.get("return_data")==result["return_data"],"raw metadata/result join")
                need(result["events"]==[s for s in result["logs"]if s.startswith("Program data: ")],"event ordered log projection")
                # Recompute the retained Pump/Tokenkeg CPI projections from metadata.
                pump=[];token_calls=[]
                for group in result["inner"]:
                    for entry in group:
                        ix=entry["instruction"];data=bytes(ix["data"][1:]);accounts=[keys[k]for k in ix["accounts"][1:]];pid=keys[ix["programIdIndex"]]
                        if pid==PUMP and data.startswith(bytes([225,154,117,22,215,86,246,103])):
                            need(list(data[20:])==([2,1]if case["sell"]else[1,2])and len(accounts)==23 and accounts[2]==a["keys"][3],"inner Pump source flags/roles")
                            pump.append(dict(amount=struct.unpack_from("<Q",data,8)[0],flags=list(data[20:]),accounts=accounts))
                        if pid==TOKEN:token_calls.append(dict(data_hex=data.hex(),accounts=accounts))
                need(pump==result["pump_calls"]and token_calls==result["token_calls"],"inner call projection")
                need(len(observation["loads"])==1,"one captured Pump load")
                receipt=dict(observation["loads"][0]);need(isinstance(receipt.pop("input_path"),str),"loader input label")
                need(receipt==load_receipts[label],"captured loader actual image/allocation/zero-tail join");loads+=1
                program_hashes=dict(dependency_hashes,**{PUMP:hashes[label]})
                need(result["program_sha256"]==program_hashes and observation["program_loads"]==[dict(program=pid,sha256=program_hashes[pid])for pid,_ in PROGRAMS]+[dict(program=PUMP,sha256=hashes[label])],"all actual loaded program hashes")
                if label!="original":
                    for field in ["error","events","inner","return_data","before","after","transaction_base64","pump_calls","token_calls"]:need(result[field]==runs["original"][field],"actual structured parity: "+field)
                    need(logs(result)==logs(runs["original"]),"actual ordered non-compute log parity")
                expected_error=expected_errors[i]if family=="regression"else "6041"if family=="zeroquote"else None
                need(result["error"]is None if expected_error is None else isinstance(result["error"],str)and expected_error in result["error"],"declared observed outcome")
                if family=="zeroquote":need(any("trade_v3.rs:317"in s and "6041"in s for s in result["logs"]),"upstream fee gate, not zero-quote helper coverage")
            need(row["proposal_differences"]==row["parent_differences"]==[]and row["proposal_log_equal"]is True and row.get("parent_log_equal",True)is True,"retained parity summaries")
            successes+=runs["original"]["error"]is None;outcomes.append(dict(case=case["name"],error=runs["original"]["error"]))
    need(signed==48 and loads==48 and successes==7,"16 triples/48 signatures/7 original successes")
    return dict(case_triples=16,executions=48,verified_signatures=signed,captured_loader_records=loads,original_successes=successes,structured_or_ordered_log_mismatches=0,upstream_gate_cases=1,zero_quote_helper_runtime_coverage=False,receipts=receipt_report,outcomes=outcomes,limitations=["Retained reports are not independent execution attestation.","No independent post-state snapshot; complete post-state is compared across the three reports.","Host runtime executable fingerprints are pinned receipt provenance, not reexecuted."])
