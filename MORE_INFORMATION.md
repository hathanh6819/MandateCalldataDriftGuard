# More Information

## Steward Request: Authenticate the Bytes Ultimately Executed

The steward requested:

> Thanks for the submission. What held this back is that the ticket is based on a human-written decoding and is not coupled to the transaction ultimately executed. A qualifying version should authenticate raw calldata against an ABI and make a downstream executor atomically require the ticket for those exact bytes.

This review item is implemented in Mandate / Calldata Drift Guard v3 and exercised on Studionet.

## What Changed

V2 accepted a human-written decoded call manifest. V3 removes that evidence path completely.

The deployed guard now receives:

- one canonical function ABI;
- raw calldata;
- target contract;
- chain ID;
- native value;
- bounded expiry;
- proposal revision; and
- the execution wallet that may consume the ticket.

The guard deterministically derives the Ethereum function selector from:

```text
keccak256(functionName(type1,type2,...))[0:4]
```

It requires all three identities to match:

```text
selector derived from ABI signature
== selector declared in canonical ABI
== first four bytes of raw calldata
```

The guard also requires an exact ABI-sized payload. It rejects missing words, extra trailing words, non-canonical address padding, non-canonical booleans, unsupported types, malformed ABI and malformed hex before decentralized judgment can run.

## Deterministic Decoding, Not Human-Written Decoding

V3 supports a deliberately bounded static ABI surface:

- `address`
- `uint256`
- `bool`
- `bytes32`

Each argument is decoded directly from the raw 32-byte ABI word. The model never receives a claimant-authored action description. It receives only the deterministic ticket and decoded values produced by contract code.

For the live `transfer(address,uint256)` case, the deployed guard decoded:

```text
recipient = 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
amount = 50000
```

The complete raw bytes were committed as:

```text
calldata_keccak256 = 378d7369566ca0e433376db2387af8cca9c146ee353be7fd6c7482b5301c0062
calldata_sha256    = 2732859dd58966a293f4bb97d6817858d4915907c85040810f27cc6d004b048e
```

## Ticket Binding

An authorization ticket is bound to all execution-critical fields:

```text
proposal ID
revision
chain ID
target
native value
function selector
function name
ABI SHA-256
raw calldata Keccak-256
raw calldata SHA-256
expiry
bound execution wallet
```

Changing the selector, recipient, amount, calldata length, target, chain, value, revision, expiry or caller cannot reuse the ticket.

## Downstream Executor Requirement

V3 includes a separate deployed `GuardedCalldataExecutor`.

The guard's execution method performs this sequence in one state transition:

```text
require bound execution wallet
require current revision
require ALIGNED verdict
require unused ticket
require unexpired ticket
require current chain ID
require exact calldata Keccak-256 and SHA-256
mark ticket consumed
increment execution nonce
emit exact raw calldata to downstream executor on finalization
```

The downstream executor independently requires:

```text
message.sender_address == deployed guard address
```

It rejects direct calls from wallets or unrelated contracts. After receiving the authenticated bytes from the guard, the reference executor independently decodes the exact `transfer(address,uint256)` bytes and applies the amount to its persistent credit ledger.

This couples the ticket to a real downstream state transition. The executor does not accept a separate human-written amount or recipient.

## Conflict Proof: Silence Did Not Grant Target Authority

The first live proposal authorized the function, recipient, amount and zero native value, but did not explicitly authorize the target executor address.

Assessment correctly finalized:

```text
target_allowed = false
material_drift = true
status = MATERIAL_DRIFT
```

No execution capability was granted. The project retains this result as evidence that the semantic gate does not infer target authority from silence.

- Conflict assessment: [`0x4a23fe5804e8c52c2b53c4c25065da6d0f7d17fd2fc6a776254da8a1b84b0807`](https://explorer-studio.genlayer.com/tx/0x4a23fe5804e8c52c2b53c4c25065da6d0f7d17fd2fc6a776254da8a1b84b0807)

## Happy-Path Proof: Exact Policy and Exact Bytes

A second proposal explicitly authorized:

- target `0x9746D0529DbbA87f93F526F115802EeCfb10a7b6`;
- chain ID `61999`;
- function `transfer(address,uint256)`;
- recipient `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`;
- maximum amount `50000`; and
- zero native value.

The assessment finalized `ALIGNED` with every required predicate true and `material_drift=false`:

- Lock exact bytes: [`0x4cc2992767a47ecf824b87fade244acc002b6340981cdf0d5bae491ffd323518`](https://explorer-studio.genlayer.com/tx/0x4cc2992767a47ecf824b87fade244acc002b6340981cdf0d5bae491ffd323518)
- Assess exact bytes: [`0x907eced3921448fd1268b2d61152d31c698206378fb7d0807c891a91c87568a9`](https://explorer-studio.genlayer.com/tx/0x907eced3921448fd1268b2d61152d31c698206378fb7d0807c891a91c87568a9)
- Execute exact bytes: [`0x1edbcf3e16297222f825b4d5b5864f73f2921ec52f4dc1e58af54027ab0c71e9`](https://explorer-studio.genlayer.com/tx/0x1edbcf3e16297222f825b4d5b5864f73f2921ec52f4dc1e58af54027ab0c71e9)

Final readback proved:

```text
guard status = EXECUTION_QUEUED
consumed = true
execution_nonce = 1
executor execution_count = 1
executor total_executed = 50000
recipient credit balance = 50000
executor raw_calldata = exact locked raw_calldata
```

## Adversarial Live Proof

### ABI/selector mismatch

The ABI declared `transfer(address,uint256)` while the calldata selector was changed. The transaction failed and the proposal remained `DRAFT`.

- [`0x96c57e3fe5d097078ba32cb6899afade6325b34d1d07af470512ccf1bca2bce1`](https://explorer-studio.genlayer.com/tx/0x96c57e3fe5d097078ba32cb6899afade6325b34d1d07af470512ccf1bca2bce1)

### Wrong execution wallet

The governance wallet attempted to consume a ticket bound to the separate execution wallet. The transaction failed and the complete proposal state remained unchanged.

- [`0x1308d04a5158ce09c7f0d6ada30b7b7cf6da28b75eeee908186626496ddce179`](https://explorer-studio.genlayer.com/tx/0x1308d04a5158ce09c7f0d6ada30b7b7cf6da28b75eeee908186626496ddce179)

### One-byte calldata mutation

The bound execution wallet changed one hexadecimal digit in the encoded amount. Exact-byte verification rejected the transaction and preserved the unused ticket.

- [`0x0259f54ab52811dea3af0a0b5f4b29c5dbc3f7dedc2a9cec7dc33433b149e257`](https://explorer-studio.genlayer.com/tx/0x0259f54ab52811dea3af0a0b5f4b29c5dbc3f7dedc2a9cec7dc33433b149e257)

### Replay

After successful execution, the same wallet submitted the same exact bytes again. The transaction failed; the execution nonce remained one and the downstream ledger was unchanged.

- [`0x681fcb677dc44719d1779a8a154e05c307eee5c0da2ba8aab54fda6f58e9f859`](https://explorer-studio.genlayer.com/tx/0x681fcb677dc44719d1779a8a154e05c307eee5c0da2ba8aab54fda6f58e9f859)

## Automated Behavioral Verification

The release gate passes:

- Direct Mode contract tests: **16 passed**
- Frontend rule tests: **5 passed**
- Guard GenVM lint/schema validation: **PASS**
- Executor GenVM lint/schema validation: **PASS**
- Frontend production build: **PASS**
- Production dependency audit: **0 vulnerabilities**

Automated coverage includes:

- exact ABI decoding;
- selector/signature mismatch;
- malformed ABI;
- unsupported ABI types;
- missing and trailing calldata words;
- recipient mutation;
- amount mutation;
- semantic material drift;
- invalid model output;
- wrong executor wallet;
- wrong chain;
- stale revision;
- expiry;
- revocation;
- direct downstream invocation; and
- replay.

## Reviewed Deployments

Studionet guard v3:

[`0xC7F60004fA18E54786938B93E79205389C2f4AE1`](https://explorer-studio.genlayer.com/address/0xC7F60004fA18E54786938B93E79205389C2f4AE1)

Repository guard source SHA-256:

`07d4f42d120f9651919535089ca2e2b39ed8e5624c78b1cfc9bc5e955a578f4c`

Studionet guarded executor:

[`0x9746D0529DbbA87f93F526F115802EeCfb10a7b6`](https://explorer-studio.genlayer.com/address/0x9746D0529DbbA87f93F526F115802EeCfb10a7b6)

Repository executor source SHA-256:

`b5eced3715b0b7a7c11fd2835d35b8e0ce821bfe22b95437230d5d5fab0e04b7`

Production frontend:

[https://mandate-calldata-drift-guard.pages.dev/](https://mandate-calldata-drift-guard.pages.dev/)

Complete transaction table and final readback:

[`verification/studionet-v3-lifecycle.md`](verification/studionet-v3-lifecycle.md)

## Platform Boundary

The downstream target demonstrated here is a GenLayer Intelligent Contract. It performs a real persistent credit-ledger transition from the authenticated `transfer(address,uint256)` bytes.

GenLayer documentation states that Studio does not currently implement arbitrary EVM contract interaction beyond value transfers. The project therefore does not claim that Studionet executed arbitrary Solidity `target.call(rawCalldata)`. It proves the requested security property using a real Guard-to-Intelligent-Contract execution path: the downstream executor cannot run without a valid ticket for the exact authenticated bytes.
