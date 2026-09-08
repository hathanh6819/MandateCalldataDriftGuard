# Design and threat model

## Proof obligation

Before issuing a single-use execution ticket, establish that every effect in a fixed decoded call manifest is explicitly covered by a fixed DAO mandate: targets and recipients are disclosed, amounts do not exceed authority, no privilege or upgrade is introduced, and ordering does not create an undisclosed effect.

The evidence does **not** prove that a DAO vote occurred or that arbitrary bytes will be executed by an external chain. Deployment explicitly binds a separate governance-authority wallet. That authority registers the governance identity, repository, executor and policy; the deploying wallet receives no operational method. The ticket is an authorization receipt for the exact committed manifest; an integrating executor must separately bind its actual execution to that manifest.

## Evidence topology

This mechanism uses a paired-document proof rather than a single beneficial narrative. The authority fixes one repository and policy at proposal creation. A revision then fixes one Git commit, two distinct paths, both complete-byte SHA-256 commitments and an expiry. Validators independently fetch both GitHub raw artifacts. Deterministic code checks size, digest, shared identities, call count, order indices, target addresses, selectors, values and decoded action bounds before the model runs.

The model compares each decoded effect against the mandate and returns only six booleans. Strict consensus covers every consequential boolean. `ALIGNED` requires five positive predicates to be exactly true and `material_drift` to be exactly false. Error, missing data, malformed output, mismatch or uncertainty becomes `UNRESOLVED`.

## Consequence and lifecycle

```text
DRAFT → PENDING → ALIGNED | MATERIAL_DRIFT | UNRESOLVED
                         ↓
                 CONSUMED (exact executor, revision, digest, expiry; once)

Any unused revision may be superseded or revoked by governance.
```

Assessment never executes a call. `consume_execution_ticket` is a separate deterministic boundary restricted to the registered executor. It checks current revision, `ALIGNED`, exact bundle digest, fresh expiry and unused state, then atomically increments a per-proposal execution nonce. Failed calls cannot increment it.

## Threat model

- Attacker wants an execution ticket for a hidden recipient, increased transfer, extra call, unsafe ordering or privilege escalation.
- They may submit misleading decoded text through a governance-controlled repository, but cannot change the repository, policy, executor, fixed commit, hashes or revision after locking without an owner transition visible on-chain.
- Full-byte digests prevent content substitution. Shared identities prevent cross-proposal and cross-contract reuse.
- Deterministic call-shape checks prevent malformed manifests from reaching semantic judgment.
- Any single false positive prerequisite blocks `ALIGNED`; wrong executor, changed digest, stale revision, expiry and replay are rejected deterministically.
- Honest limitation: the deployed contract validates a decoded manifest, not raw EVM calldata or an external Governor vote. Production integration must authenticate decoding and make the downstream executor consume this ticket before executing the same bundle.

## Material distinction

This is not a renamed vesting or evidence-release gate. It compares two independently committed artifacts, deterministically validates an ordered multi-call graph, reaches a six-dimensional semantic compatibility verdict, and issues an exact-manifest ticket to a separately bound executor. It has no custody, token ledger, payout, beneficiary, milestone, cancellation semantics or linear schedule. Persistent behavior is an execution nonce and consumed bundle authorization, not asset accounting.
