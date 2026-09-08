#!/usr/bin/env python3
"""Run the deployment-bound Studionet lifecycle. Never deploys or stores keys."""

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
DRIFT_PATH = "fixtures/adversarial/bundle-hidden-admin.json"
DRIFT_DIGEST = "f8b4d8e917557c86076cea823448274399d66bc784306250fcb39c3bda9944e0"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def check(condition, message):
    if not condition:
        raise RuntimeError("CHECKPOINT FAILED: " + message)
    print("CHECKPOINT OK: " + message, flush=True)


def read(client):
    value = client.read_contract(address=CONTRACT, function_name="get_proposal", args=[1])
    print("READ proposal=" + canonical(value), flush=True)
    return value


def write(client, method, args):
    tx = client.write_contract(address=CONTRACT, function_name=method, args=args, value=0)
    print("WRITE " + method + " tx=" + str(tx), flush=True)
    receipt = client.wait_for_transaction_receipt(
        tx, status=TransactionStatus.FINALIZED, interval=3000, retries=500,
        full_transaction=False,
    )
    print("FINAL " + method + " status=" + str(receipt.get("status_name")) + " result=" + str(receipt.get("result_name")), flush=True)
    return str(tx)


def lock(client, bundle_path, bundle_digest, mandate_digest=MANDATE_DIGEST):
    expiry = int(time.time()) + 5 * 24 * 60 * 60
    return write(client, "lock_revision", [1, COMMIT, MANDATE_PATH, mandate_digest, bundle_path, bundle_digest, expiry])


def main():
    authority_key = getpass.getpass("Governance test-wallet private key: ").strip()
    executor_key = getpass.getpass("Executor test-wallet private key: ").strip()
    authority = create_account(authority_key)
    executor = create_account(executor_key)
    authority_key = executor_key = ""
    check(str(authority.address).lower() == AUTHORITY.lower(), "wallet A identity")
    check(str(executor.address).lower() == EXECUTOR.lower(), "wallet B identity")
    governance = create_client(chain=studionet, account=authority)
    execution = create_client(chain=studionet, account=executor)
    txs = {}

    start = read(governance)
    check(start["revision"] == 0 and start["status"] == "DRAFT", "fresh registered proposal")

    txs["lock_bad_digest"] = lock(governance, ALIGNED_PATH, ALIGNED_DIGEST, "0" * 64)
    check(read(governance)["revision"] == 1, "bad-digest revision locked")
    txs["assess_bad_digest"] = write(governance, "assess_drift", [1, 1])
    bad = read(governance)
    check(bad["status"] == "UNRESOLVED" and bad["findings"] == {"reason": "DIGEST_MISMATCH"}, "fetched-byte mismatch fails closed")

    txs["lock_material_drift"] = lock(governance, DRIFT_PATH, DRIFT_DIGEST)
    txs["assess_material_drift"] = write(governance, "assess_drift", [1, 2])
    drift = read(governance)
    check(drift["status"] == "MATERIAL_DRIFT" and not drift["ticket_used"] and drift["execution_nonce"] == 0, "hidden admin grant cannot authorize execution")
    before = canonical(drift)
    txs["consume_drift_blocked"] = write(execution, "consume_execution_ticket", [1, 2, DRIFT_DIGEST])
    check(canonical(read(governance)) == before, "rejected drift consumption preserves complete state")

    txs["lock_recovery"] = lock(governance, ALIGNED_PATH, ALIGNED_DIGEST)
    txs["assess_aligned"] = write(governance, "assess_drift", [1, 3])
    aligned = read(governance)
    check(aligned["status"] == "ALIGNED" and len(aligned["receipt"]) == 64, "canonical evidence reaches bounded ALIGNED state")

    before = canonical(aligned)
    txs["wrong_actor_consume"] = write(governance, "consume_execution_ticket", [1, 3, ALIGNED_DIGEST])
    check(canonical(read(governance)) == before, "wrong actor rollback preserves complete state")
    txs["stale_revision_consume"] = write(execution, "consume_execution_ticket", [1, 2, ALIGNED_DIGEST])
    check(canonical(read(governance)) == before, "stale revision rollback preserves complete state")
    txs["changed_bundle_consume"] = write(execution, "consume_execution_ticket", [1, 3, "f" * 64])
    check(canonical(read(governance)) == before, "changed bundle rollback preserves complete state")

    txs["consume_exact_ticket"] = write(execution, "consume_execution_ticket", [1, 3, ALIGNED_DIGEST])
    consumed = read(governance)
    check(consumed["status"] == "CONSUMED" and consumed["ticket_used"] and consumed["execution_nonce"] == 1, "wallet B consumes exact ticket once")
    before = canonical(consumed)
    txs["replay_blocked"] = write(execution, "consume_execution_ticket", [1, 3, ALIGNED_DIGEST])
    check(canonical(read(governance)) == before, "replay rollback preserves terminal state and nonce")

    print("LIFECYCLE_COMPLETE", flush=True)
    print("transactions=" + canonical(txs), flush=True)


if __name__ == "__main__":
    main()
