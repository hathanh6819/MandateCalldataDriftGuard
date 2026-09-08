#!/usr/bin/env python3
"""Register the first live proposal with the governance test wallet. Never deploys."""

import getpass
import json
import os

from genlayer_py import create_account, create_client, studionet
from genlayer_py.types.transactions import TransactionStatus

CONTRACT = os.environ.get("DRIFT_GUARD_ADDRESS", "0x3A0Bd8668420e5132B77c3626C9A1c2eac45Eeb6")
AUTHORITY = "0x1D283b45974B0be9630DFD1deC6A62a9B72B2760"
EXECUTOR = "0xf96Cf822F9f4e76956AB9fAAa22B3BdCD7b10aD6"
REPOSITORY = "hathanh6819/MandateCalldataDriftGuard"
GOVERNANCE_ID = "DAO-CALLDATA-2026-001"
POLICY = "Every target, recipient, amount, privilege and call ordering must be explicitly authorized by the approved mandate. Silence grants no authority."


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main():
    secret = getpass.getpass("Governance test-wallet private key: ").strip()
    account = create_account(secret)
    secret = ""
    if str(account.address).lower() != AUTHORITY.lower():
        raise SystemExit("The supplied key is not governance test wallet A")
    client = create_client(chain=studionet, account=account)
    info = client.read_contract(address=CONTRACT, function_name="get_info", args=[])
    if str(info.get("governance_authority", "")).lower() != AUTHORITY.lower():
        raise SystemExit("Deployed governance authority does not match wallet A")
    if int(info.get("proposal_count", -1)) != 0:
        print("Proposal already exists; refusing duplicate registration")
        print(canonical(client.read_contract(address=CONTRACT, function_name="get_proposal", args=[1])))
        return
    tx = client.write_contract(
        address=CONTRACT,
        function_name="register_proposal",
        args=[GOVERNANCE_ID, EXECUTOR, REPOSITORY, POLICY],
        value=0,
    )
    print("register_proposal tx=" + str(tx), flush=True)
    receipt = client.wait_for_transaction_receipt(
        tx, status=TransactionStatus.FINALIZED, interval=3000, retries=400,
        full_transaction=False,
    )
    print("receipt=" + canonical(receipt), flush=True)
    proposal = client.read_contract(address=CONTRACT, function_name="get_proposal", args=[1])
    print("proposal=" + canonical(proposal), flush=True)
    if proposal.get("status") != "DRAFT" or str(proposal.get("executor", "")).lower() != EXECUTOR.lower():
        raise SystemExit("Final readback does not match the registered proposal")


if __name__ == "__main__":
    main()
