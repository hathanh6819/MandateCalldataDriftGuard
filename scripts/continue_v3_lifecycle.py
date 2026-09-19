#!/usr/bin/env python3
import getpass,json,time
from genlayer_py import create_account,create_client,studionet
from genlayer_py.types.transactions import TransactionStatus
GUARD="0xC7F60004fA18E54786938B93E79205389C2f4AE1"; TARGET="0x9746D0529DbbA87f93F526F115802EeCfb10a7b6"; AUTH="0x1D283b45974B0be9630DFD1deC6A62a9B72B2760"; EXEC="0xf96Cf822F9f4e76956AB9fAAa22B3BdCD7b10aD6"; RECIPIENT="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
POLICY=f"Authorize target {TARGET.lower()} on chain 61999 to execute only transfer(address,uint256) to {RECIPIENT} for at most 50000 credit units with zero native value. No other target, recipient, function, amount, privilege or value is authorized."
ABI=json.dumps({"type":"function","name":"transfer","selector":"0xa9059cbb","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}]},separators=(",",":")); RAW="0xa9059cbb"+"0"*24+RECIPIENT[2:]+format(50000,"064x")
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),default=str)
def read(c,m,a=[]):return c.read_contract(address=GUARD,function_name=m,args=a)
def write(c,m,a):
 tx=c.write_contract(address=GUARD,function_name=m,args=a,value=0);print(m+" tx="+str(tx),flush=True);r=c.wait_for_transaction_receipt(tx,status=TransactionStatus.FINALIZED,interval=3000,retries=500,full_transaction=False);print(m+" final="+str(r.get("result_name")),flush=True);return str(tx)
def ok(v,s):
 if not v:raise RuntimeError("FAILED: "+s)
 print("CHECKPOINT OK: "+s,flush=True)
def main():
 ka=getpass.getpass("Governance key: ").strip();kb=getpass.getpass("Execution key: ").strip();a=create_account(ka);b=create_account(kb);ka=kb="";ok(str(a.address).lower()==AUTH.lower(),"wallet A");ok(str(b.address).lower()==EXEC.lower(),"wallet B");ca=create_client(chain=studionet,account=a);cb=create_client(chain=studionet,account=b);tx={}
 p1=read(ca,"get_proposal",[1]);ok(p1["status"]=="MATERIAL_DRIFT" and not p1["consumed"],"proposal 1 conflict preserved")
 tx["register_exact_policy"]=write(ca,"register_proposal",["DAO-CALLDATA-V3-002",EXEC,POLICY]);expiry=int(time.time())+5*86400
 tx["lock_exact"]=write(ca,"lock_calldata",[2,0,TARGET,studionet.id,0,ABI,RAW,expiry]);tx["assess_exact"]=write(ca,"assess_calldata",[2,1]);p=read(ca,"get_proposal",[2]);ok(p["status"]=="ALIGNED","explicit target policy reaches ALIGNED")
 before=canon(p);tx["wrong_wallet"]=write(ca,"execute_exact_calldata",[2,1,RAW]);ok(canon(read(ca,"get_proposal",[2]))==before,"wrong wallet rollback")
 changed=RAW[:-1]+("1" if RAW[-1]!="1" else "2");tx["changed_byte"]=write(cb,"execute_exact_calldata",[2,1,changed]);ok(canon(read(cb,"get_proposal",[2]))==before,"changed byte rollback")
 tx["execute_exact"]=write(cb,"execute_exact_calldata",[2,1,RAW]);p=read(cb,"get_proposal",[2]);ok(p["consumed"] and p["execution_nonce"]==1,"ticket consumed exactly once")
 for i in range(20):
  e=cb.read_contract(address=TARGET,function_name="get_execution",args=[])
  if e["execution_count"]==1:break
  time.sleep(5)
 ok(e["execution_count"]==1 and e["total_executed"]==50000 and e["raw_calldata"]==RAW,"child executor applied exact bytes");ok(cb.read_contract(address=TARGET,function_name="balance_of",args=[RECIPIENT])==50000,"recipient ledger effect")
 before=canon(p);tx["replay"]=write(cb,"execute_exact_calldata",[2,1,RAW]);ok(canon(read(cb,"get_proposal",[2]))==before,"replay rollback")
 print("LIFECYCLE_COMPLETE\ntransactions="+canon(tx)+"\nproposal="+canon(p)+"\nexecutor="+canon(e))
if __name__=="__main__":main()
