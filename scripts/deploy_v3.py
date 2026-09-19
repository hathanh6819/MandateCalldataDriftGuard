#!/usr/bin/env python3
"""Deploy v3 guard and reference executor. Keys are hidden and never persisted."""
import getpass, json
from pathlib import Path
from genlayer_py import create_account, create_client, studionet
from genlayer_py.types.transactions import TransactionStatus

ROOT=Path(__file__).resolve().parents[1]

def finalized(client,tx):
    receipt=client.wait_for_transaction_receipt(tx,status=TransactionStatus.FINALIZED,interval=3000,retries=500,full_transaction=False)
    address=receipt.get("contract_address")
    if not address: raise RuntimeError("deployment finalized without contract address: "+json.dumps(receipt,default=str))
    return str(address)

def main():
    governance_key=getpass.getpass("Governance wallet private key: ").strip()
    execution_key=getpass.getpass("Execution wallet private key: ").strip()
    governance=create_account(governance_key); execution=create_account(execution_key)
    governance_key=execution_key=""
    print("governance="+str(governance.address)); print("execution="+str(execution.address),flush=True)
    client=create_client(chain=studionet,account=governance)
    guard_code=(ROOT/"contracts"/"mandate_calldata_drift_guard.py").read_text(encoding="utf-8")
    guard_tx=client.deploy_contract(code=guard_code,args=[str(governance.address)])
    print("guard_deploy_tx="+str(guard_tx),flush=True); guard=finalized(client,guard_tx); print("guard="+guard,flush=True)
    executor_code=(ROOT/"contracts"/"guarded_calldata_executor.py").read_text(encoding="utf-8")
    executor_tx=client.deploy_contract(code=executor_code,args=[guard])
    print("executor_deploy_tx="+str(executor_tx),flush=True); executor=finalized(client,executor_tx); print("executor="+executor,flush=True)
    print("RESULT="+json.dumps({"network":"Studionet","chain_id":studionet.id,"guard":guard,"executor":executor,"governance":str(governance.address),"execution_wallet":str(execution.address),"guard_deploy_tx":str(guard_tx),"executor_deploy_tx":str(executor_tx)},separators=(",",":")),flush=True)

if __name__=="__main__": main()
