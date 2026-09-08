# Mandate / Calldata Drift Guard

A GenLayer dApp that detects material drift between an approved DAO mandate and a fixed decoded transaction bundle before issuing a bounded, single-use execution ticket.

## Why GenLayer

Deterministic code can verify repositories, commits, hashes, identities and call shapes, but cannot reliably decide whether a decoded action is actually disclosed by a natural-language mandate. Validators independently fetch both artifacts and reach strict consensus over the exact semantic predicates that control authorization.

## Safety properties

- Authority-fixed repository, policy and executor.
- Two separate, fixed-commit GitHub artifacts with complete-byte SHA-256 recomputation.
- Contract/proposal/governance/executor identity binding in both documents.
- At most eight calls; deterministic index, target, selector, value and text validation.
- Every positive semantic prerequisite is mandatory; uncertainty fails closed.
- Assessment and ticket consumption are separate transitions.
- Exact executor, revision, digest and expiry binding.
- Atomic one-use nonce and replay rejection.
- No mock state, fallback verdict or sample balances in the frontend.

## Local verification

```powershell
python -m pytest
genvm-lint check contracts/mandate_calldata_drift_guard.py --json
cd frontend
npm ci
npm test
npm run build
npm run dev
```

Current verification: 23 direct real-contract tests pass; GenVM lint and semantic validation pass; 3 frontend rule tests pass; production build passes; production dependency audit reports zero vulnerabilities.

## Deployment

Deploy `contracts/mandate_calldata_drift_guard.py` on Studionet with no constructor arguments. The deploying wallet becomes the governance authority. Do not publish evidence fixtures before deployment: both documents must include the exact deployed address and created proposal ID. Configure `VITE_CONTRACT_ADDRESS` only after deployed-source parity and live `get_info` have been verified.

See `docs/DESIGN.md` for proof boundary, threat model, lifecycle and the explicit downstream-executor limitation.
