# Mandate / Calldata Drift Guard v3

A GenLayer execution firewall that authenticates raw calldata against a canonical ABI, judges the decoded action against a governance mandate, and makes a downstream Intelligent Contract require the resulting exact-byte, single-use ticket.

## What changed after steward review

V2 trusted a human-written decoded manifest. V3 removes that path completely. The contract now receives raw calldata and ABI, derives and checks the Ethereum selector, deterministically decodes bounded static arguments, commits the complete bytes, and gates a real downstream message on the ticket. The reference executor rejects direct invocation and applies the authenticated `transfer(address,uint256)` bytes to its on-chain credit ledger.

## Safety properties

- Selector derived from Keccak-256 of `function(type,...)`.
- ABI selector and raw calldata prefix equality.
- Canonical static ABI decoding with no ignored trailing bytes.
- Complete raw calldata Keccak-256 and SHA-256 commitments.
- Ticket binds proposal, revision, chain ID, target, value, selector, ABI hash, calldata hash and expiry.
- Governance-only locking, bound-wallet execution, one-use consumption and replay rejection.
- Downstream executor requires the guard as caller.
- Uncertainty and semantic drift fail closed.

## Local verification

```powershell
python -m pytest -q
genvm-lint check contracts/mandate_calldata_drift_guard.py --json
genvm-lint check contracts/guarded_calldata_executor.py --json
cd frontend
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

## Deployment status

V3 is deployed on Studionet:

- Guard: [`0xC7F60004fA18E54786938B93E79205389C2f4AE1`](https://explorer-studio.genlayer.com/address/0xC7F60004fA18E54786938B93E79205389C2f4AE1)
- Executor: [`0x9746D0529DbbA87f93F526F115802EeCfb10a7b6`](https://explorer-studio.genlayer.com/address/0x9746D0529DbbA87f93F526F115802EeCfb10a7b6)
- Verified lifecycle: [verification/studionet-v3-lifecycle.md](verification/studionet-v3-lifecycle.md)

## Platform boundary

The reference target is a GenLayer Intelligent Contract reached through a finalized internal message. Studio does not currently implement arbitrary EVM contract calls beyond value transfers, so the repository does not claim otherwise. See [docs/DESIGN.md](docs/DESIGN.md).
