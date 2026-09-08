#!/usr/bin/env python3
"""Continue after a safe consensus rollback at adversarial revision 2."""

import getpass
import json
import time

from genlayer_py import create_account, create_client, studionet
from genlayer_py.types.transactions import TransactionStatus

CONTRACT = "0x3A0Bd8668420e5132B77c3626C9A1c2eac45Eeb6"
AUTHORITY = "0x1D283b45974B0be9630DFD1deC6A62a9B72B2760"
EXECUTOR = "0xf96Cf822F9f4e76956AB9fAAa22B3BdCD7b10aD6"
COMMIT = "dd4ebae0ccb77e5f7cad6cf984c5e64f8b4faa73"
MANDATE_PATH = "fixtures/canonical/mandate.json"
MANDATE_DIGEST = "e9dd35e6b1c2e796e292239e79404c4c838d59602a834ccefce330e3ce71fb46"
ALIGNED_PATH = "fixtures/canonical/bundle.json"
ALIGNED_DIGEST = "144255a741ce83c6778b466a789ad37b5a8bf178facb03718f320cc7500f24f4"

def canon(v): return json.dumps(v, sort_keys=True, separators=(",", ":"))
def check(ok, msg):
    if not ok: raise RuntimeError("CHECKPOINT FAILED: " + msg)
    print("CHECKPOINT OK: " + msg, flush=True)
def read(c):
    v=c.read_contract(address=CONTRACT,function_name="get_proposal",args=[1]); print("READ proposal="+canon(v),flush=True); return v
def write(c,m,a):
    tx=c.write_contract(address=CONTRACT,function_name=m,args=a,value=0); print("WRITE "+m+" tx="+str(tx),flush=True)
    r=c.wait_for_transaction_receipt(tx,status=TransactionStatus.FINALIZED,interval=3000,retries=500,full_transaction=False)
    print("FINAL "+m+" status="+str(r.get("status_name"))+" result="+str(r.get("result_name")),flush=True); return str(tx),str(r.get("result_name"))

def main():
    ak=getpass.getpass("Governance test-wallet private key: ").strip(); ek=getpass.getpass("Executor test-wallet private key: ").strip()
    aa=create_account(ak); ea=create_account(ek); ak=ek=""
    check(str(aa.address).lower()==AUTHORITY.lower(),"wallet A identity"); check(str(ea.address).lower()==EXECUTOR.lower(),"wallet B identity")
    gov=create_client(chain=studionet,account=aa); exe=create_client(chain=studionet,account=ea); txs={}
    state=read(gov); check(state["revision"]==2 and state["status"]=="PENDING" and state["execution_nonce"]==0,"consensus rollback preserved adversarial revision")
    for attempt in range(1,4):
        tx,result=write(gov,"assess_drift",[1,2]); txs["assess_material_drift_retry_"+str(attempt)]=tx; state=read(gov)
        if state["status"]=="MATERIAL_DRIFT": break
        check(state["status"]=="PENDING" and state["execution_nonce"]==0,"non-agree retry remains fail-closed")
    check(state["status"]=="MATERIAL_DRIFT" and not state["ticket_used"],"hidden admin grant classified as material drift")
    before=canon(state); txs["consume_drift_blocked"]=write(exe,"consume_execution_ticket",[1,2,state["evidence"]["bundle_digest"]])[0]; check(canon(read(gov))==before,"drift consume rollback preserves state")
    expiry=int(time.time())+5*24*60*60
    txs["lock_recovery"]=write(gov,"lock_revision",[1,COMMIT,MANDATE_PATH,MANDATE_DIGEST,ALIGNED_PATH,ALIGNED_DIGEST,expiry])[0]
    txs["assess_aligned"]=write(gov,"assess_drift",[1,3])[0]; aligned=read(gov); check(aligned["status"]=="ALIGNED" and len(aligned["receipt"])==64,"aligned evidence authorizes exact ticket")
    before=canon(aligned)
    for label,client,rev,digest in [("wrong_actor",gov,3,ALIGNED_DIGEST),("stale_revision",exe,2,ALIGNED_DIGEST),("changed_bundle",exe,3,"f"*64)]:
        txs[label]=write(client,"consume_execution_ticket",[1,rev,digest])[0]; check(canon(read(gov))==before,label+" rollback preserves complete state")
    txs["consume_exact_ticket"]=write(exe,"consume_execution_ticket",[1,3,ALIGNED_DIGEST])[0]; consumed=read(gov); check(consumed["status"]=="CONSUMED" and consumed["ticket_used"] and consumed["execution_nonce"]==1,"wallet B consumes once")
    before=canon(consumed); txs["replay_blocked"]=write(exe,"consume_execution_ticket",[1,3,ALIGNED_DIGEST])[0]; check(canon(read(gov))==before,"replay preserves terminal state")
    print("LIFECYCLE_COMPLETE",flush=True); print("transactions="+canon(txs),flush=True)

if __name__=="__main__": main()
