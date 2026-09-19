# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from genlayer.py.keccak import Keccak256
import hashlib, json, re
from datetime import datetime

MAX_CALLDATA_BYTES = 1024
MAX_ABI_BYTES = 6000
HEX40 = re.compile(r"^0x[0-9a-f]{40}$")
HEXDATA = re.compile(r"^0x[0-9a-f]+$")
SUPPORTED_TYPES = ("address", "uint256", "bool", "bytes32")

def encode(value): return json.dumps(value, sort_keys=True, separators=(",", ":"))
def require(ok, message):
    if not ok: raise gl.vm.UserError(message)
def addr(value):
    text = str(value).lower()
    if text.startswith("address(") and "0x" in text: text = "0x" + text.split("0x",1)[1].split(")",1)[0]
    if not text.startswith("0x"):
        try: text = "0x" + format(int(value), "040x")
        except Exception: pass
    return text
def now(): return int(datetime.fromisoformat(str(gl.message_raw["datetime"]).replace("Z", "+00:00")).timestamp())
def raw_bytes(raw):
    text = raw.strip().lower()
    require(HEXDATA.fullmatch(text) is not None and len(text) % 2 == 0, "INVALID_CALLDATA_HEX")
    value = bytes.fromhex(text[2:])
    require(4 <= len(value) <= MAX_CALLDATA_BYTES, "INVALID_CALLDATA_LENGTH")
    return text, value
def parse_abi(abi_json):
    require(0 < len(abi_json.encode()) <= MAX_ABI_BYTES, "INVALID_ABI_SIZE")
    try: abi = json.loads(abi_json)
    except Exception: raise gl.vm.UserError("INVALID_ABI_JSON")
    require(type(abi) is dict and set(abi) == {"type","name","selector","inputs"}, "INVALID_ABI_SHAPE")
    require(abi["type"] == "function" and type(abi["name"]) is str and 1 <= len(abi["name"]) <= 80, "INVALID_ABI_FUNCTION")
    require(type(abi["selector"]) is str and re.fullmatch(r"0x[0-9a-f]{8}", abi["selector"]) is not None, "INVALID_ABI_SELECTOR")
    require(type(abi["inputs"]) is list and 1 <= len(abi["inputs"]) <= 8, "INVALID_ABI_INPUTS")
    for item in abi["inputs"]:
        require(type(item) is dict and set(item) == {"name","type"}, "INVALID_ABI_INPUT")
        require(type(item["name"]) is str and 1 <= len(item["name"]) <= 80 and item["type"] in SUPPORTED_TYPES, "UNSUPPORTED_ABI_INPUT")
    signature = abi["name"] + "(" + ",".join(item["type"] for item in abi["inputs"]) + ")"
    require("0x" + Keccak256(signature.encode()).hexdigest()[:8] == abi["selector"], "SELECTOR_SIGNATURE_MISMATCH")
    return abi
def decode_static(abi, data):
    require(data[:4].hex() == abi["selector"][2:], "SELECTOR_ABI_MISMATCH")
    require(len(data) == 4 + 32 * len(abi["inputs"]), "CALLDATA_ABI_LENGTH_MISMATCH")
    result = []
    for index, item in enumerate(abi["inputs"]):
        word = data[4+32*index:36+32*index]; kind = item["type"]
        if kind == "address":
            require(word[:12] == b"\x00"*12, "NON_CANONICAL_ADDRESS"); value = "0x" + word[12:].hex()
        elif kind == "uint256": value = str(int.from_bytes(word, "big"))
        elif kind == "bool":
            number = int.from_bytes(word, "big"); require(number in (0,1), "NON_CANONICAL_BOOL"); value = number == 1
        else: value = "0x" + word.hex()
        result.append(dict(name=item["name"], type=kind, value=value))
    return result

class MandateCalldataDriftGuard(gl.Contract):
    governance_authority: str
    count: u256
    records: TreeMap[u256, str]

    def __init__(self, governance_authority: Address):
        authority = addr(governance_authority)
        require(HEX40.fullmatch(authority) is not None and authority != "0x"+"0"*40, "INVALID_GOVERNANCE_AUTHORITY")
        self.governance_authority = authority; self.count = u256(0)

    def _load(self, proposal_id):
        require(0 < int(proposal_id) <= int(self.count), "UNKNOWN_PROPOSAL")
        return json.loads(self.records[proposal_id])

    @gl.public.write
    def register_proposal(self, governance_id: str, executor: Address, policy: str) -> int:
        require(addr(gl.message.sender_address) == self.governance_authority, "ONLY_GOVERNANCE_AUTHORITY")
        executor_text = addr(executor)
        require(1 <= len(governance_id) <= 96 and 30 <= len(policy) <= 4000, "INVALID_MANDATE")
        require(HEX40.fullmatch(executor_text) is not None and executor_text != "0x"+"0"*40, "INVALID_EXECUTOR")
        self.count += u256(1); pid = int(self.count)
        self.records[pid] = encode(dict(id=pid, governance_id=governance_id, executor=executor_text, policy=policy, revision=0, status="DRAFT", ticket=None, findings=None, decoded=[], consumed=False, execution_nonce=0, execution_message=""))
        return pid

    @gl.public.write
    def lock_calldata(self, proposal_id: u256, expected_revision: u256, target: Address, chain_id: u256, value: u256, abi_json: str, raw_calldata: str, expiry: u256) -> int:
        require(addr(gl.message.sender_address) == self.governance_authority, "ONLY_GOVERNANCE_AUTHORITY")
        record = self._load(proposal_id)
        require(int(expected_revision) == record["revision"], "STALE_REVISION")
        require(not record["consumed"], "TICKET_ALREADY_USED")
        target_text = addr(target); require(HEX40.fullmatch(target_text) is not None and target_text != "0x"+"0"*40, "INVALID_TARGET")
        require(int(chain_id) > 0 and now() < int(expiry) <= now()+604800, "INVALID_SCOPE_OR_EXPIRY")
        abi = parse_abi(abi_json); raw_text, data = raw_bytes(raw_calldata); decoded = decode_static(abi, data)
        revision = record["revision"] + 1
        ticket = dict(proposal_id=int(proposal_id), revision=revision, chain_id=int(chain_id), target=target_text, value=str(int(value)), selector=abi["selector"], function=abi["name"], calldata_keccak256=Keccak256(data).hexdigest(), calldata_sha256=hashlib.sha256(data).hexdigest(), abi_sha256=hashlib.sha256(encode(abi).encode()).hexdigest(), expiry=int(expiry))
        record.update(revision=revision, status="PENDING", ticket=ticket, findings=None, decoded=decoded, consumed=False, execution_message="")
        self.records[proposal_id] = encode(record); return revision

    @gl.public.write
    def assess_calldata(self, proposal_id: u256, revision: u256) -> str:
        record = self._load(proposal_id)
        require(int(revision) == record["revision"], "STALE_REVISION")
        require(record["status"] in ("PENDING","UNRESOLVED"), "REVIEW_CLOSED")
        require(now() < record["ticket"]["expiry"], "EXPIRED")
        prompt = """Compare the approved governance mandate with the deterministically ABI-decoded transaction below. The decoded fields are authenticated from raw calldata, not human-written descriptions. Return ONLY JSON with exactly target_allowed, function_allowed, arguments_allowed, value_allowed, material_drift as booleans. Silence grants no authority. Any extra recipient, larger amount, privilege grant, upgrade, ownership change, target change, function change, or value increase is material drift.\nPOLICY\n""" + record["policy"] + "\nBOUND TRANSACTION\n" + encode(dict(ticket=record["ticket"], decoded=record["decoded"]))
        def evaluate():
            try:
                result = gl.nondet.exec_prompt(prompt, response_format="json")
                if isinstance(result, str): result = json.loads(result)
                keys = {"target_allowed","function_allowed","arguments_allowed","value_allowed","material_drift"}
                if type(result) is not dict or set(result) != keys or any(type(v) is not bool for v in result.values()): return encode(dict(status="UNRESOLVED", reason="INVALID_FINDINGS"))
                return encode(dict(status="ASSESSED", findings=result))
            except Exception: return encode(dict(status="UNRESOLVED", reason="MODEL_ERROR"))
        result = json.loads(gl.eq_principle.strict_eq(evaluate))
        if result["status"] != "ASSESSED": record["status"]="UNRESOLVED"; record["findings"]={"reason":result["reason"]}
        else:
            findings=result["findings"]; aligned=all(findings[k] for k in ("target_allowed","function_allowed","arguments_allowed","value_allowed")) and not findings["material_drift"]
            record["status"]="ALIGNED" if aligned else "MATERIAL_DRIFT"; record["findings"]=findings
        self.records[proposal_id]=encode(record); return record["status"]

    @gl.public.write
    def execute_exact_calldata(self, proposal_id: u256, revision: u256, raw_calldata: str) -> str:
        record=self._load(proposal_id); ticket=record["ticket"]
        require(addr(gl.message.sender_address)==record["executor"], "ONLY_BOUND_EXECUTOR")
        require(int(revision)==record["revision"], "STALE_REVISION")
        require(record["status"]=="ALIGNED" and not record["consumed"], "NOT_AUTHORIZED")
        require(now()<ticket["expiry"], "EXPIRED")
        raw_text,data=raw_bytes(raw_calldata)
        require(Keccak256(data).hexdigest()==ticket["calldata_keccak256"] and hashlib.sha256(data).hexdigest()==ticket["calldata_sha256"], "CALLDATA_CHANGED")
        require(int(gl.message_raw["chain_id"])==ticket["chain_id"], "CHAIN_CHANGED")
        receipt=hashlib.sha256(encode(dict(ticket=ticket,raw_calldata=raw_text,executor=record["executor"])).encode()).hexdigest()
        record["consumed"]=True; record["status"]="EXECUTION_QUEUED"; record["execution_nonce"]+=1; record["execution_message"]=receipt
        self.records[proposal_id]=encode(record)
        gl.get_contract_at(Address(ticket["target"])).emit(on="finalized").execute_calldata(raw_text,receipt)
        return receipt

    @gl.public.write
    def revoke(self, proposal_id: u256) -> str:
        require(addr(gl.message.sender_address)==self.governance_authority,"ONLY_GOVERNANCE_AUTHORITY")
        record=self._load(proposal_id); require(not record["consumed"],"TICKET_ALREADY_USED")
        record["revision"]+=1; record["status"]="REVOKED"; record["findings"]=None; self.records[proposal_id]=encode(record); return "REVOKED"

    @gl.public.view
    def get_info(self) -> dict: return dict(name="MandateCalldataDriftGuard",version=3,governance_authority=self.governance_authority,proposal_count=int(self.count),max_calldata_bytes=MAX_CALLDATA_BYTES)
    @gl.public.view
    def get_proposal(self, proposal_id: u256) -> dict: return self._load(proposal_id)
