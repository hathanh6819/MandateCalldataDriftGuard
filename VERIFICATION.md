# V3 verification status

## Automated release gates

- Both contracts pass GenVM lint and schema validation.
- Direct tests cover ABI decoding, selector authentication, byte hashes, happy-path message emission and single-use consumption.
- Adversarial tests mutate selector, recipient, amount and calldata length/trailing bytes.
- Failure tests cover malformed ABI, unsupported types, semantic drift, invalid model output, wrong executor, stale revision, wrong chain, expiry, revoke and direct executor invocation.
- Frontend tests cover ABI/raw decoding, malformed inputs and finalized-receipt checks.

## Live evidence

The previous v2 evidence was removed because it authenticated human-written manifests and does not prove v3. The complete two-wallet v3 lifecycle is recorded in [`verification/studionet-v3-lifecycle.md`](verification/studionet-v3-lifecycle.md).

Completed checkpoints:

1. Deployed `MandateCalldataDriftGuard` v3 with the governance wallet.
2. Deploy `GuardedCalldataExecutor` with the new guard address.
3. Register a proposal binding the execution wallet and explicit policy.
4. Lock ABI plus raw calldata with target = executor and the actual chain ID.
5. Assess to `ALIGNED`.
6. Execute with the bound wallet and capture parent plus triggered child transaction.
7. Read back guard state (`EXECUTION_QUEUED`, consumed, nonce 1) and executor state (same bytes and receipt, execution count 1, recipient balance increased by the exact decoded amount).
8. Record changed-byte, wrong-wallet, stale, expired and replay failures with unchanged state.
9. Bound the frontend production environment to the new guard and rebuilt it. Cloudflare redeployment is the final release step.
