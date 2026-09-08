import hashlib, json, pytest
from datetime import datetime, timezone

AUTHORITY = "0x1111111111111111111111111111111111111111"
EXECUTOR = "0x2222222222222222222222222222222222222222"
OUTSIDER = "0x3333333333333333333333333333333333333333"
T = 1893456000
POLICY = "Every target, recipient, amount, privilege and call ordering must be explicitly authorized by the approved mandate. Silence grants no authority."
ALIGNED = dict(all_calls_disclosed=True, amounts_within_mandate=True, recipients_within_mandate=True, privileges_within_mandate=True, ordering_safe=True, material_drift=False)

def address(value):
    from genlayer.py.types import Address
    return Address(value)
def warp(vm, timestamp): vm.warp(datetime.fromtimestamp(timestamp, timezone.utc).isoformat())

@pytest.fixture
def setup(direct_vm, direct_deploy):
    warp(direct_vm, T)
    c = direct_deploy("contracts/mandate_calldata_drift_guard.py", AUTHORITY)
    with direct_vm.prank(address(AUTHORITY)):
        assert c.register_proposal("DAO-42", address(EXECUTOR), "dao/mandates", POLICY) == 1
    return c, direct_vm

def docs(vm, **changes):
    contract = address(vm._contract_address) if isinstance(vm._contract_address, bytes) else vm._contract_address
    common = dict(contract=str(contract.as_hex).lower(), proposal_id=1, governance_id="DAO-42", executor=EXECUTOR)
    mandate = dict(**common, mandate="Transfer exactly 50000 USDC to 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for the audited research grant. No upgrades, role grants, ownership changes, extra recipients or additional calls are authorized.")
    bundle = dict(**common, calls=[dict(index=0,target="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",selector="0xa9059cbb",value=0,decoded_action="Transfer exactly 50000 USDC to 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")])
    if "mandate" in changes: mandate.update(changes["mandate"])
    if "bundle" in changes: bundle.update(changes["bundle"])
    return json.dumps(mandate, separators=(",", ":")).encode(), json.dumps(bundle, separators=(",", ":")).encode()

def prepare(c, vm, mandate=None, bundle=None, hashes=None, statuses=(200,200), findings=None):
    default_m, default_b = docs(vm)
    mandate, bundle = mandate or default_m, bundle or default_b
    md, bd = hashes or (hashlib.sha256(mandate).hexdigest(), hashlib.sha256(bundle).hexdigest())
    with vm.prank(address(AUTHORITY)):
        rev = c.lock_revision(1, "a"*40, "mandate.json", md, "bundle.json", bd, T+5000)
    vm.clear_mocks()
    vm.mock_web(r"mandate\.json$", dict(status=statuses[0], body=mandate.decode(errors="replace")))
    vm.mock_web(r"bundle\.json$", dict(status=statuses[1], body=bundle.decode(errors="replace")))
    vm.mock_llm("Compare an approved DAO mandate", json.dumps(findings or ALIGNED))
    return rev

def as_executor(c, vm, method, *args):
    with vm.prank(address(EXECUTOR)):
        from genlayer.gl.vm import UserError
        try: return getattr(c, method)(*args)
        except UserError as error: return str(error)

def test_happy_path_consumes_exact_bundle_once(setup):
    c, vm = setup; mandate, bundle = docs(vm); rev = prepare(c, vm, mandate, bundle)
    digest = hashlib.sha256(bundle).hexdigest()
    assert c.assess_drift(1, rev) == "ALIGNED"
    reviewed = c.get_proposal(1); assert len(reviewed["receipt"]) == 64 and not reviewed["ticket_used"]
    assert as_executor(c, vm, "consume_execution_ticket", 1, rev, digest) == reviewed["receipt"]
    consumed = c.get_proposal(1); assert consumed["status"] == "CONSUMED" and consumed["execution_nonce"] == 1
    assert "NOT_AUTHORIZED" in as_executor(c, vm, "consume_execution_ticket", 1, rev, digest)
    assert c.get_proposal(1) == consumed

@pytest.mark.parametrize("field", ["all_calls_disclosed","amounts_within_mandate","recipients_within_mandate","privileges_within_mandate","ordering_safe"])
def test_every_positive_prerequisite_is_mandatory(setup, field):
    c, vm = setup; findings = dict(ALIGNED); findings[field] = False; rev = prepare(c, vm, findings=findings)
    assert c.assess_drift(1, rev) == "MATERIAL_DRIFT"
    assert "NOT_AUTHORIZED" in as_executor(c, vm, "consume_execution_ticket", 1, rev, "0"*64)

def test_material_drift_blocks_ticket(setup):
    c, vm = setup; findings = dict(ALIGNED, material_drift=True); rev = prepare(c, vm, findings=findings)
    assert c.assess_drift(1, rev) == "MATERIAL_DRIFT"
    assert c.get_proposal(1)["execution_nonce"] == 0

@pytest.mark.parametrize("kind", ["mandate_digest","bundle_digest","mandate_identity","bundle_identity","shape","oversized","unavailable","model"])
def test_sources_and_bindings_fail_closed(setup, kind):
    c, vm = setup; mandate, bundle = docs(vm); hashes=None; statuses=(200,200); findings=ALIGNED
    if kind == "mandate_digest": hashes=("f"*64, hashlib.sha256(bundle).hexdigest())
    elif kind == "bundle_digest": hashes=(hashlib.sha256(mandate).hexdigest(), "f"*64)
    elif kind == "mandate_identity": mandate, bundle = docs(vm, mandate={"proposal_id":2})
    elif kind == "bundle_identity": mandate, bundle = docs(vm, bundle={"executor":OUTSIDER})
    elif kind == "shape": mandate=b"not-json"
    elif kind == "oversized": mandate=b"x"*16001
    elif kind == "unavailable": statuses=(404,200)
    elif kind == "model": findings=dict(ALIGNED, ordering_safe="true")
    rev=prepare(c,vm,mandate,bundle,hashes,statuses,findings)
    assert c.assess_drift(1,rev)=="UNRESOLVED"
    before=c.get_proposal(1)
    assert "NOT_AUTHORIZED" in as_executor(c,vm,"consume_execution_ticket",1,rev,before["evidence"]["bundle_digest"])
    assert c.get_proposal(1)==before

def test_invalid_call_manifest_fails_before_ai(setup):
    c,vm=setup; mandate,bundle=docs(vm,bundle={"calls":[dict(index=0,target=OUTSIDER,selector="bad",value=0,decoded_action="hidden admin grant")]}); rev=prepare(c,vm,mandate,bundle)
    assert c.assess_drift(1,rev)=="UNRESOLVED"
    assert c.get_proposal(1)["findings"]=={"reason":"INVALID_CALL_MANIFEST"}

def test_wrong_executor_and_changed_bundle_cannot_consume(setup):
    c,vm=setup; mandate,bundle=docs(vm); rev=prepare(c,vm,mandate,bundle); digest=hashlib.sha256(bundle).hexdigest(); assert c.assess_drift(1,rev)=="ALIGNED"
    from genlayer.gl.vm import UserError
    before=c.get_proposal(1)
    with pytest.raises(UserError,match="ONLY_BOUND_EXECUTOR"): c.consume_execution_ticket(1,rev,digest)
    assert "BUNDLE_CHANGED" in as_executor(c,vm,"consume_execution_ticket",1,rev,"f"*64)
    assert c.get_proposal(1)==before

def test_deployer_and_executor_cannot_act_as_governance(setup):
    c,vm=setup
    from genlayer.gl.vm import UserError
    before=c.get_proposal(1)
    with pytest.raises(UserError,match="ONLY_GOVERNANCE_AUTHORITY"):
        c.lock_revision(1,"a"*40,"m.json","a"*64,"b.json","b"*64,T+100)
    with vm.prank(address(EXECUTOR)):
        with pytest.raises(UserError,match="ONLY_GOVERNANCE_AUTHORITY"):
            c.revoke(1)
    assert c.get_proposal(1)==before

def test_stale_expiry_revoke_and_recovery(setup):
    c,vm=setup; rev=prepare(c,vm,statuses=(503,200)); assert c.assess_drift(1,rev)=="UNRESOLVED"
    mandate,bundle=docs(vm); rev2=prepare(c,vm,mandate,bundle)
    from genlayer.gl.vm import UserError
    with pytest.raises(UserError,match="STALE_REVISION"): c.assess_drift(1,rev)
    assert c.assess_drift(1,rev2)=="ALIGNED"; warp(vm,T+5000)
    assert "EXPIRED" in as_executor(c,vm,"consume_execution_ticket",1,rev2,hashlib.sha256(bundle).hexdigest())
    warp(vm,T)
    with vm.prank(address(AUTHORITY)): c.revoke(1)
    assert c.get_proposal(1)["status"]=="REVOKED"

@pytest.mark.parametrize("index,value", [(0,""),(1,"0x0000000000000000000000000000000000000000"),(2,"../repo"),(3,"short")])
def test_invalid_registration_preserves_count(direct_vm,direct_deploy,index,value):
    warp(direct_vm,T); c=direct_deploy("contracts/mandate_calldata_drift_guard.py",AUTHORITY); args=["DAO-42",address(EXECUTOR),"dao/mandates",POLICY]; args[index]=address(value) if index==1 else value
    from genlayer.gl.vm import UserError
    with direct_vm.prank(address(AUTHORITY)):
        with pytest.raises(UserError): c.register_proposal(*args)
    assert c.get_info()["proposal_count"]==0

def test_validator_falsifies_changed_semantics(setup, monkeypatch):
    c,vm=setup; rev=prepare(c,vm); assert c.assess_drift(1,rev)=="ALIGNED"
    import genlayer.gl.vm as gl_vm
    monkeypatch.setattr(gl_vm,"spawn_sandbox",lambda fn: gl_vm.Return(fn()))
    assert vm.run_validator() is True
    mandate,bundle=docs(vm); vm.clear_mocks(); vm.mock_web(r"mandate\.json$",dict(status=200,body=mandate.decode())); vm.mock_web(r"bundle\.json$",dict(status=200,body=bundle.decode())); vm.mock_llm("Compare an approved DAO mandate",json.dumps(dict(ALIGNED,material_drift=True)))
    assert vm.run_validator() is False
