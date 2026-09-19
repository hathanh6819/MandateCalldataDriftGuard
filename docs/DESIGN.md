# V3 design and threat model

## Proof obligation

The guard authenticates the bytes that will be sent downstream, not a human-written decoding. Governance locks a canonical single-function ABI, target, chain ID, native value, raw calldata and expiry. Deterministic code derives the Ethereum selector from `name(types)` with Keccak-256, requires it to match both the ABI selector and the first four calldata bytes, validates canonical static ABI encoding, decodes every argument and commits both Keccak-256 and SHA-256 of the complete calldata.

Only the authenticated decoded tuple is presented to decentralized semantic judgment. `ALIGNED` requires target, function, arguments and value to be allowed and `material_drift=false`. Invalid ABI, malformed bytes, ambiguous model output or disagreement cannot authorize execution.

## Enforced execution path

```text
governance policy + canonical ABI + raw calldata
                         |
          deterministic selector/length/decode
                         |
               decentralized assessment
                         |
          exact-byte, chain, target, value ticket
                         |
       bound executor calls execute_exact_calldata
                         |
        atomic consumption + finalized IC message
                         |
       GuardedCalldataExecutor.execute_calldata
```

The downstream executor rejects direct calls from every address except the guard contract. The guard checks executor identity, revision, status, expiry, current chain and both complete-byte hashes before atomically consuming the ticket. It then emits the exact raw calldata and ticket receipt to the registered downstream Intelligent Contract on finalization. The reference executor independently decodes `transfer(address,uint256)` and applies the amount to its persistent credit ledger. Replay cannot emit a second message.

## Supported ABI surface

V3 deliberately supports bounded static inputs: `address`, `uint256`, `bool`, and `bytes32`, with one to eight inputs and at most 1,024 calldata bytes. Unsupported dynamic or nested ABI types fail closed rather than being partially decoded.

## Threat model

- Selector substitution fails because selector = Keccak-256(`name(types)`) = calldata prefix is enforced.
- Recipient, amount, boolean, bytes32, padding, length or trailing-data changes alter the exact-byte hashes and cannot consume the ticket.
- Target, chain ID, native value, revision, executor and expiry are stored in the ticket and checked at consumption.
- Only governance may register policy and lock bytes; only the bound execution wallet may trigger execution.
- Semantic drift, invalid model shape and consensus uncertainty never authorize.
- Consumption precedes message emission in one transaction; successful consumption prevents replay.
- The target executor independently requires `sender_address == guard`.

## Honest platform boundary

This implementation exercises a real GenLayer Intelligent Contract to Intelligent Contract message. GenLayer documentation states that arbitrary EVM contract interaction beyond value transfers is not implemented in Studio. Therefore this project does not claim that Studio executed arbitrary Ethereum calldata against an EVM contract. Production EVM integration can replace the reference downstream Intelligent Contract with an external-message adapter when that network feature is available, while preserving the same exact-byte ticket.
