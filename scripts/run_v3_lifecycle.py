#!/usr/bin/env python3
"""Run the v3 two-wallet Studionet lifecycle. Secrets are hidden and never stored."""
import getpass, json, time
from genlayer_py import create_account, create_client, studionet
from genlayer_py.types.transactions import TransactionStatus

GUARD="0xC7F60004fA18E54786938B93E79205389C2f4AE1"
TARGET="0x9746D0529DbbA87f93F526F115802EeCfb10a7b6"
AUTHORITY="0x1D283b45974B0be9630DFD1deC6A62a9B72B2760"
EXECUTION_WALLET="0xf96Cf822F9f4e76956AB9fAAa22B3BdCD7b10aD6"
RECIPIENT="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
POLICY="Authorize only transfer(address,uint256) to 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for at most 50000 units, with zero native value. No other target, recipient, function, amount, privilege or value is authorized."
ABI=json.dumps({"type":"function","name":"transfer","selector":"0xa9059cbb","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}]},separators=(",",":"))
RAW="0xa9059cbb"+("0"*24)+RECIPIENT[2:]+format(50000,"064x")

def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":"),default=str)
def read(client,method,args=[]): return client.read_contract(address=GUARD,function_name=method,args=args)
def write(client,method,args):
    before=None
    try: before=read(client,"get_proposal",[1])
    except Exception: pass
    tx=client.write_contract(address=GUARD,function_name=method,args=args,value=0)
    print(method+" tx="+str(tx),flush=True)
    receipt=client.wait_for_transaction_receipt(tx,status=TransactionStatus.FINALIZED,interval=3000,retries=500,full_transaction=False)
    print(method+" receipt="+canonical({"status":receipt.get("status_name"),"result":receipt.get("result_name")}),flush=True)
    return str(tx),before
def check(ok,label):
    if not ok: raise RuntimeError("CHECKPOINT FAILED: "+label)
    print("CHECKPOINT OK: "+label,flush=True)

def main():
    key_a=getpass.getpass("Governance test-wallet private key: ").strip(); key_b=getpass.getpass("Execution test-wallet private key: ").strip()
    a=create_account(key_a); b=create_account(key_b); key_a=key_b=""
    check(str(a.address).lower()==AUTHORITY.lower(),"wallet A identity"); check(str(b.address).lower()==EXECUTION_WALLET.lower(),"wallet B identity")
    ca=create_client(chain=studionet,account=a); cb=create_client(chain=studionet,account=b); txs={}
    info=read(ca,"get_info"); check(info["version"]==3 and info["proposal_count"]==0,"fresh v3 guard")
    txs["register"],_=write(ca,"register_proposal",["DAO-CALLDATA-V3-001",EXECUTION_WALLET,POLICY])
    draft=read(ca,"get_proposal",[1]); check(draft["status"]=="DRAFT" and draft["executor"].lower()==EXECUTION_WALLET.lower(),"proposal binds execution wallet")
    expiry=int(time.time())+5*24*60*60
    txs["abi_mismatch"],before=write(ca,"lock_calldata",[1,0,TARGET,studionet.id,0,ABI,"0x095ea7b3"+RAW[10:],expiry])
    check(read(ca,"get_proposal",[1])==before,"ABI mismatch rolls back")
    txs["lock_exact"],_=write(ca,"lock_calldata",[1,0,TARGET,studionet.id,0,ABI,RAW,expiry])
    locked=read(ca,"get_proposal",[1]); check(locked["status"]=="PENDING" and locked["decoded"][1]["value"]=="50000","raw bytes decoded on-chain")
    txs["assess"],_=write(ca,"assess_calldata",[1,1])
    aligned=read(ca,"get_proposal",[1]); check(aligned["status"]=="ALIGNED","semantic assessment authorizes exact bytes")
    txs["wrong_wallet"],before=write(ca,"execute_exact_calldata",[1,1,RAW]); check(read(ca,"get_proposal",[1])==before,"wrong wallet rolls back")
    changed=RAW[:-1]+("1" if RAW[-1]!="1" else "2")
    txs["changed_byte"],before=write(cb,"execute_exact_calldata",[1,1,changed]); check(read(cb,"get_proposal",[1])==before,"changed byte rolls back")
    txs["execute_exact"],_=write(cb,"execute_exact_calldata",[1,1,RAW])
    consumed=read(cb,"get_proposal",[1]); check(consumed["status"]=="EXECUTION_QUEUED" and consumed["consumed"] and consumed["execution_nonce"]==1,"ticket consumed once")
    print("Waiting for finalized child message...",flush=True); time.sleep(20)
    execution=cb.read_contract(address=TARGET,function_name="get_execution",args=[])
    check(execution["execution_count"]==1 and execution["total_executed"]==50000 and execution["raw_calldata"]==RAW,"downstream effect executed exact bytes")
    check(cb.read_contract(address=TARGET,function_name="balance_of",args=[RECIPIENT])==50000,"recipient credit balance increased")
    txs["replay"],before=write(cb,"execute_exact_calldata",[1,1,RAW]); check(read(cb,"get_proposal",[1])==before,"replay rolls back")
    print("LIFECYCLE_COMPLETE"); print("transactions="+canonical(txs)); print("guard="+canonical(consumed)); print("executor="+canonical(execution))

if __name__=="__main__": main()
