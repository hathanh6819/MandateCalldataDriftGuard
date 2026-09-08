# Verification record

- Contract tests: 24 passed.
- Exact contract source SHA-256: `690efff12faa20540fc948d65a29027b8e9b7205b0c2fb75961fb473dcf2fc1d`.
- GenVM lint: passed.
- GenVM semantic validation must report one constructor parameter: the governance authority, distinct from deployer and executor.
- Frontend tests: 3 passed.
- Frontend production build: 454 modules transformed successfully.
- Production dependency audit: 0 vulnerabilities.
- Logo SHA-256: `ab1ebd6f07d967d6025864d957077fabbd88d3c92d431338e5747bb1d4c0ca9`; the supplied PNG is used unchanged.

## Required live gates

1. Deploy exact source with test wallet A as governance authority and compare complete deployed-source SHA-256. The primary wallet performs deployment only.
2. Register a proposal with a distinct executor wallet.
3. Publish deployment-bound aligned and adversarial evidence pairs at immutable commits.
4. Run aligned, hidden-call/privilege, digest mismatch, identity mismatch, stale revision, expiry, recovery, wrong executor, changed bundle and replay paths on Studionet.
5. Confirm failed paths preserve `ticket_used=false` and `execution_nonce=0`; confirm the valid path increments exactly once.
6. Bind the frontend to the verified address, test wallet/account/network changes and one signed production journey.

Until these gates are complete, the project is locally verified and **not submission-ready**.
