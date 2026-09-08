# Studionet bootstrap

- Contract: `0x3A0Bd8668420e5132B77c3626C9A1c2eac45Eeb6`
- Deployment readback: version `2`, proposal count `0`, deployer `0xa365f55a3bf352767bc5c5739ffddaee8fcf3a19`, governance authority `0x1d283b45974b0be9630dfd1dec6a62a9b72b2760`.
- Governance registration transaction: `0x04b3960d4fca06893c5f098ad39eba3f6977bb4bad0781cd057dd806f43896e5`
- Registration finality: `FINALIZED`, consensus result `MAJORITY_AGREE`, leader execution `SUCCESS`.
- Proposal readback: ID `1`, governance identity `DAO-CALLDATA-2026-001`, executor `0xf96cf822f9f4e76956ab9faaa22b3bdcd7b10ad6`, status `DRAFT`, revision `0`, `ticket_used=false`, `execution_nonce=0`.

The primary deployment wallet did not register the proposal. Governance test wallet A performed the registration; test wallet B remains the bound execution authority.

## Deployment-bound fixture digests

- `fixtures/canonical/mandate.json`: `e9dd35e6b1c2e796e292239e79404c4c838d59602a834ccefce330e3ce71fb46`
- `fixtures/canonical/bundle.json`: `144255a741ce83c6778b466a789ad37b5a8bf178facb03718f320cc7500f24f4`
- `fixtures/adversarial/bundle-hidden-admin.json`: `f8b4d8e917557c86076cea823448274399d66bc784306250fcb39c3bda9944e0`

These are hashes of the exact local bytes. Assessment must not begin until the files are published to the registered GitHub repository at a fixed full commit and the raw responses reproduce these values.
