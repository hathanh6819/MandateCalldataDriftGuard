# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import re

def addr(value):
    text=str(value).lower()
    if text.startswith("address(") and "0x" in text: text="0x"+text.split("0x",1)[1].split(")",1)[0]
    if not text.startswith("0x"):
        try: text="0x"+format(int(value),"040x")
        except Exception: pass
    return text

class GuardedCalldataExecutor(gl.Contract):
    guard: str
    execution_count: u256
    last_calldata: str
    last_ticket_receipt: str
    total_executed: u256
    credits: TreeMap[str, u256]

    def __init__(self, guard: Address):
        self.guard=addr(guard); self.execution_count=u256(0); self.last_calldata=""; self.last_ticket_receipt=""; self.total_executed=u256(0)

    @gl.public.write
    def execute_calldata(self, raw_calldata: str, ticket_receipt: str) -> None:
        if addr(gl.message.sender_address)!=self.guard: raise gl.vm.UserError("ONLY_GUARD")
        text=raw_calldata.strip().lower()
        if re.fullmatch(r"0x[0-9a-f]+",text) is None or len(text)<10 or len(text)%2!=0: raise gl.vm.UserError("INVALID_CALLDATA")
        if re.fullmatch(r"[0-9a-f]{64}",ticket_receipt) is None: raise gl.vm.UserError("INVALID_TICKET_RECEIPT")
        data=bytes.fromhex(text[2:])
        if len(data)!=68 or data[:4].hex()!="a9059cbb" or data[4:16]!=b"\x00"*12: raise gl.vm.UserError("UNSUPPORTED_EXECUTION_CALL")
        recipient="0x"+data[16:36].hex(); amount=int.from_bytes(data[36:68],"big")
        if amount==0: raise gl.vm.UserError("ZERO_AMOUNT")
        self.credits[recipient]=self.credits.get(recipient,u256(0))+u256(amount)
        self.total_executed+=u256(amount); self.execution_count+=u256(1); self.last_calldata=text; self.last_ticket_receipt=ticket_receipt

    @gl.public.view
    def get_execution(self) -> dict:
        return dict(guard=self.guard,execution_count=int(self.execution_count),total_executed=int(self.total_executed),raw_calldata=self.last_calldata,ticket_receipt=self.last_ticket_receipt)

    @gl.public.view
    def balance_of(self, recipient: Address) -> int:
        return int(self.credits.get(addr(recipient),u256(0)))
