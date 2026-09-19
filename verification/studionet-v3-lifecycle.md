# Studionet v3 exact-calldata lifecycle

Run date: 2026-09-19

- Guard v3: [`0xC7F60004fA18E54786938B93E79205389C2f4AE1`](https://explorer-studio.genlayer.com/address/0xC7F60004fA18E54786938B93E79205389C2f4AE1)
- Guarded executor: [`0x9746D0529DbbA87f93F526F115802EeCfb10a7b6`](https://explorer-studio.genlayer.com/address/0x9746D0529DbbA87f93F526F115802EeCfb10a7b6)
- Network: GenLayer Studionet, chain ID 61999
- Governance and execution used two distinct test wallets. Keys were entered through hidden prompts and were not stored.

## Transactions

| Scenario | Finalized outcome | Transaction |
| --- | --- | --- |
| Register proposal 1 | Bound policy and execution wallet | [`0xcf6c982cd2056795afa48908097b48dc1a8b23f04b1518c374c21d953f06afa3`](https://explorer-studio.genlayer.com/tx/0xcf6c982cd2056795afa48908097b48dc1a8b23f04b1518c374c21d953f06afa3) |
| ABI selector mismatch | Rejected; draft state unchanged | [`0x96c57e3fe5d097078ba32cb6899afade6325b34d1d07af470512ccf1bca2bce1`](https://explorer-studio.genlayer.com/tx/0x96c57e3fe5d097078ba32cb6899afade6325b34d1d07af470512ccf1bca2bce1) |
| Lock exact calldata, proposal 1 | Selector, arguments and complete-byte hashes persisted | [`0x0fcd7f79c020b5e14b2268428f6daa96d786e5dbc6e297f7e431635e30dc9435`](https://explorer-studio.genlayer.com/tx/0x0fcd7f79c020b5e14b2268428f6daa96d786e5dbc6e297f7e431635e30dc9435) |
| Assess policy missing target | `MATERIAL_DRIFT`; no authorization | [`0x4a23fe5804e8c52c2b53c4c25065da6d0f7d17fd2fc6a776254da8a1b84b0807`](https://explorer-studio.genlayer.com/tx/0x4a23fe5804e8c52c2b53c4c25065da6d0f7d17fd2fc6a776254da8a1b84b0807) |
| Register explicit policy, proposal 2 | Policy names exact target, function, recipient, cap, chain and value | [`0x9da5a6c31ea1cab9f944cefa78bffaa061bed01a6c7855e08bad523e0f13eae5`](https://explorer-studio.genlayer.com/tx/0x9da5a6c31ea1cab9f944cefa78bffaa061bed01a6c7855e08bad523e0f13eae5) |
| Lock exact calldata, proposal 2 | Raw `transfer(address,uint256)` decoded and committed | [`0x4cc2992767a47ecf824b87fade244acc002b6340981cdf0d5bae491ffd323518`](https://explorer-studio.genlayer.com/tx/0x4cc2992767a47ecf824b87fade244acc002b6340981cdf0d5bae491ffd323518) |
| Assess exact policy | `ALIGNED`; all five predicates safe | [`0x907eced3921448fd1268b2d61152d31c698206378fb7d0807c891a91c87568a9`](https://explorer-studio.genlayer.com/tx/0x907eced3921448fd1268b2d61152d31c698206378fb7d0807c891a91c87568a9) |
| Wrong wallet execute | Rejected; full state unchanged | [`0x1308d04a5158ce09c7f0d6ada30b7b7cf6da28b75eeee908186626496ddce179`](https://explorer-studio.genlayer.com/tx/0x1308d04a5158ce09c7f0d6ada30b7b7cf6da28b75eeee908186626496ddce179) |
| One-byte amount mutation | Rejected; full state unchanged | [`0x0259f54ab52811dea3af0a0b5f4b29c5dbc3f7dedc2a9cec7dc33433b149e257`](https://explorer-studio.genlayer.com/tx/0x0259f54ab52811dea3af0a0b5f4b29c5dbc3f7dedc2a9cec7dc33433b149e257) |
| Execute exact calldata | Ticket consumed; finalized child executor effect | [`0x1edbcf3e16297222f825b4d5b5864f73f2921ec52f4dc1e58af54027ab0c71e9`](https://explorer-studio.genlayer.com/tx/0x1edbcf3e16297222f825b4d5b5864f73f2921ec52f4dc1e58af54027ab0c71e9) |
| Replay | Rejected; nonce remains one, ledger unchanged | [`0x681fcb677dc44719d1779a8a154e05c307eee5c0da2ba8aab54fda6f58e9f859`](https://explorer-studio.genlayer.com/tx/0x681fcb677dc44719d1779a8a154e05c307eee5c0da2ba8aab54fda6f58e9f859) |

## Final readback

- Proposal 2: `EXECUTION_QUEUED`, `consumed=true`, `execution_nonce=1`.
- Decoded recipient: `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`.
- Decoded amount: `50000`.
- Calldata Keccak-256: `378d7369566ca0e433376db2387af8cca9c146ee353be7fd6c7482b5301c0062`.
- Calldata SHA-256: `2732859dd58966a293f4bb97d6817858d4915907c85040810f27cc6d004b048e`.
- Executor: `execution_count=1`, `total_executed=50000`, recipient credit balance `50000`.
- Executor stored the exact raw calldata and ticket receipt `de3323c677b87a6d7e3ac2b31552a8067746eb11450c277a1379f2433420ed8a`.

The conflict path is intentionally retained: when policy omitted the target, validators refused authorization. The successful path required explicit target authority rather than inferring it from silence.
