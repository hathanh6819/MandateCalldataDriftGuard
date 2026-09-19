import json, pytest
from datetime import datetime, timezone

AUTHORITY="0x1111111111111111111111111111111111111111"; EXECUTOR="0x2222222222222222222222222222222222222222"; TARGET="0x3333333333333333333333333333333333333333"; RECIPIENT="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"; OUTSIDER="0x4444444444444444444444444444444444444444"
T=1893456000; CHAIN=1337
POLICY="Authorize only transfer(address,uint256) to 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for at most 50000 units, with zero native value. No other target, recipient, function, amount, privilege or value is authorized."
ABI=json.dumps({"type":"function","name":"transfer","selector":"0xa9059cbb","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}]},separators=(",",":"))
RAW="0xa9059cbb"+("0"*24)+RECIPIENT[2:]+format(50000,"064x")
ALIGNED=dict(target_allowed=True,function_allowed=True,arguments_allowed=True,value_allowed=True,material_drift=False)

def address(value):
    from genlayer.py.types import Address
    return Address(value)
def warp(vm,timestamp): vm.warp(datetime.fromtimestamp(timestamp,timezone.utc).isoformat())
@pytest.fixture
def setup(direct_vm,direct_deploy):
    warp(direct_vm,T); direct_vm._chain_id=CHAIN; c=direct_deploy("contracts/mandate_calldata_drift_guard.py",AUTHORITY)
    with direct_vm.prank(address(AUTHORITY)): assert c.register_proposal("DAO-42",address(EXECUTOR),POLICY)==1
    return c,direct_vm
def lock(c,vm,raw=RAW,abi=ABI,target=TARGET,chain=CHAIN,value=0,revision=0):
    with vm.prank(address(AUTHORITY)): return c.lock_calldata(1,revision,address(target),chain,value,abi,raw,T+5000)
def assess(c,vm,findings=ALIGNED):
    vm.mock_llm("Compare the approved governance mandate",json.dumps(findings)); return c.assess_calldata(1,c.get_proposal(1)["revision"])
def user_error(call):
    from genlayer.gl.vm import UserError
    with pytest.raises(UserError) as error: call()
    return str(error.value)
class Emitter:
    def __init__(self,sink): self.sink=sink
    def emit(self,**kwargs): self.sink.append(("emit",kwargs)); return self
    def execute_calldata(self,*args): self.sink.append(("execute_calldata",args))
def patch_messages(monkeypatch,sink):
    import genlayer.gl as gl
    monkeypatch.setattr(gl,"get_contract_at",lambda target:Emitter(sink))

def test_raw_calldata_is_deterministically_decoded(setup):
    c,vm=setup; assert lock(c,vm)==1; r=c.get_proposal(1)
    assert r["ticket"]["selector"]=="0xa9059cbb" and r["ticket"]["function"]=="transfer"
    assert r["decoded"]==[{"name":"to","type":"address","value":RECIPIENT},{"name":"amount","type":"uint256","value":"50000"}]
    assert len(r["ticket"]["calldata_keccak256"])==64 and len(r["ticket"]["calldata_sha256"])==64 and len(r["ticket"]["abi_sha256"])==64

def test_happy_path_queues_exact_bytes_once(setup,monkeypatch):
    c,vm=setup; lock(c,vm); assert assess(c,vm)=="ALIGNED"; sink=[]; patch_messages(monkeypatch,sink)
    with vm.prank(address(EXECUTOR)): receipt=c.execute_exact_calldata(1,1,RAW)
    r=c.get_proposal(1); assert r["status"]=="EXECUTION_QUEUED" and r["consumed"] and r["execution_nonce"]==1 and len(receipt)==64
    assert sink[-1]==("execute_calldata",(RAW,receipt))
    with vm.prank(address(EXECUTOR)): assert "NOT_AUTHORIZED" in user_error(lambda:c.execute_exact_calldata(1,1,RAW))

@pytest.mark.parametrize("mutation",["selector","recipient","amount","extra_word"])
def test_any_calldata_mutation_is_rejected(setup,monkeypatch,mutation):
    c,vm=setup; lock(c,vm); assess(c,vm); sink=[]; patch_messages(monkeypatch,sink)
    changed={"selector":"0x095ea7b3"+RAW[10:],"recipient":RAW[:34]+("b"*40)+RAW[74:],"amount":RAW[:-1]+("1" if RAW[-1]!="1" else "2"),"extra_word":RAW+"00"*32}[mutation]
    before=c.get_proposal(1)
    with vm.prank(address(EXECUTOR)): assert "CALLDATA_CHANGED" in user_error(lambda:c.execute_exact_calldata(1,1,changed))
    assert c.get_proposal(1)==before and sink==[]

@pytest.mark.parametrize("abi,raw,message",[("not-json",RAW,"INVALID_ABI_JSON"),(json.dumps({"type":"function","name":"transfer","selector":"0x095ea7b3","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}]}),RAW,"SELECTOR_SIGNATURE_MISMATCH"),(ABI,RAW[:-2],"CALLDATA_ABI_LENGTH_MISMATCH"),(json.dumps({"type":"function","name":"x","selector":"0xa9059cbb","inputs":[{"name":"memo","type":"string"}]}),"0xa9059cbb"+"00"*32,"UNSUPPORTED_ABI_INPUT")])
def test_abi_and_raw_shape_fail_closed(setup,abi,raw,message):
    c,vm=setup
    with vm.prank(address(AUTHORITY)): assert message in user_error(lambda:c.lock_calldata(1,0,address(TARGET),CHAIN,0,abi,raw,T+5000))
    assert c.get_proposal(1)["status"]=="DRAFT"

def test_semantic_drift_never_authorizes(setup,monkeypatch):
    c,vm=setup; lock(c,vm); findings=dict(ALIGNED,arguments_allowed=False,material_drift=True)
    assert assess(c,vm,findings)=="MATERIAL_DRIFT"; sink=[]; patch_messages(monkeypatch,sink)
    with vm.prank(address(EXECUTOR)): assert "NOT_AUTHORIZED" in user_error(lambda:c.execute_exact_calldata(1,1,RAW))
    assert sink==[]
def test_invalid_model_output_is_unresolved(setup):
    c,vm=setup; lock(c,vm); assert assess(c,vm,dict(ALIGNED,arguments_allowed="true"))=="UNRESOLVED"
def test_wrong_executor_chain_revision_expiry_and_revoke(setup,monkeypatch):
    c,vm=setup; lock(c,vm); assess(c,vm); sink=[]; patch_messages(monkeypatch,sink)
    assert "ONLY_BOUND_EXECUTOR" in user_error(lambda:c.execute_exact_calldata(1,1,RAW))
    with vm.prank(address(EXECUTOR)): assert "STALE_REVISION" in user_error(lambda:c.execute_exact_calldata(1,2,RAW))
    import genlayer.gl as gl
    with vm.prank(address(EXECUTOR)):
        gl.message_raw["chain_id"]=999
        assert "CHAIN_CHANGED" in user_error(lambda:c.execute_exact_calldata(1,1,RAW))
    warp(vm,T+5000)
    with vm.prank(address(EXECUTOR)): assert "EXPIRED" in user_error(lambda:c.execute_exact_calldata(1,1,RAW))
    warp(vm,T)
    with vm.prank(address(AUTHORITY)): assert c.revoke(1)=="REVOKED"
    assert sink==[]
def test_stale_lock_and_non_authority_preserve_state(setup):
    c,vm=setup; lock(c,vm); before=c.get_proposal(1)
    with vm.prank(address(AUTHORITY)): assert "STALE_REVISION" in user_error(lambda:c.lock_calldata(1,0,address(TARGET),CHAIN,0,ABI,RAW,T+5000))
    with vm.prank(address(OUTSIDER)): assert "ONLY_GOVERNANCE_AUTHORITY" in user_error(lambda:c.lock_calldata(1,1,address(TARGET),CHAIN,0,ABI,RAW,T+5000))
    assert c.get_proposal(1)==before
def test_downstream_executor_rejects_direct_call(direct_vm,direct_deploy):
    warp(direct_vm,T); target=direct_deploy("contracts/guarded_calldata_executor.py",TARGET); before=target.get_execution()
    assert "ONLY_GUARD" in user_error(lambda:target.execute_calldata(RAW,"a"*64)); assert target.get_execution()==before
def test_downstream_executor_accepts_guard_only(direct_vm,direct_deploy):
    warp(direct_vm,T); target=direct_deploy("contracts/guarded_calldata_executor.py",TARGET)
    with direct_vm.prank(address(TARGET)): target.execute_calldata(RAW,"a"*64)
    result=target.get_execution(); assert result["execution_count"]==1 and result["total_executed"]==50000 and result["raw_calldata"]==RAW
    assert result["guard"]==TARGET
    assert target.balance_of(address(RECIPIENT))==50000
