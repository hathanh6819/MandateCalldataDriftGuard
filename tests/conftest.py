from __future__ import annotations
import os, sys, tempfile
from pathlib import Path
import pytest

FILES = []

@pytest.fixture(autouse=True)
def transaction_clock(monkeypatch):
    from gltest.direct.vm import VMContext
    original = VMContext._refresh_gl_message
    def refresh(vm):
        original(vm)
        module = sys.modules.get("genlayer.gl")
        if module is not None and hasattr(module, "message_raw"):
            module.message_raw["datetime"] = vm._datetime
    monkeypatch.setattr(VMContext, "_refresh_gl_message", refresh)

def inject(vm):
    from genlayer.py import calldata
    from genlayer.py.types import Address
    def address(value): return Address(value) if isinstance(value, bytes) else value
    data = dict(contract_address=address(vm._contract_address), sender_address=address(vm.sender), origin_address=address(vm.origin), stack=[], value=vm._value, datetime=vm._datetime, is_init=False, chain_id=vm._chain_id, entry_kind=0, entry_data=b"", entry_stage_data=None)
    fd, path = tempfile.mkstemp(prefix="gltest-mandate-")
    FILES.append(Path(path)); os.write(fd, calldata.encode(data)); os.lseek(fd, 0, os.SEEK_SET)
    vm._original_stdin_fd = os.dup(0); os.dup2(fd, 0); os.close(fd)

def pytest_configure():
    if sys.platform == "win32":
        from gltest.direct import loader
        loader._inject_message_to_fd0 = inject

def pytest_sessionfinish():
    for path in FILES:
        try: path.unlink(missing_ok=True)
        except PermissionError: pass
