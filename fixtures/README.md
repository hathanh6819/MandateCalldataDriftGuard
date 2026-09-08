# Deployment-bound fixtures

Fixtures are intentionally generated only after deployment because every document must bind the exact lowercase contract address, internal proposal ID, governance identity and executor. A pre-deployment sample could not pass contract identity checks and is not represented as live evidence.

For each test proposal, publish two UTF-8 JSON files at one full Git commit:

```json
{"contract":"0x...","proposal_id":1,"governance_id":"DAO-42","executor":"0x...","mandate":"Exact approved natural-language mandate."}
```

```json
{"contract":"0x...","proposal_id":1,"governance_id":"DAO-42","executor":"0x...","calls":[{"index":0,"target":"0x...","selector":"0xa9059cbb","value":0,"decoded_action":"Transfer exactly 50000 USDC to 0x..."}]}
```

The contract fetches both raw files, caps each response at 16,000 bytes, recomputes both SHA-256 digests, validates the shared identity tuple and validates every call shape before semantic judgment.
