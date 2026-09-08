# Studionet lifecycle evidence

Contract: `0x3A0Bd8668420e5132B77c3626C9A1c2eac45Eeb6`

Evidence commit independently fetched by validators: `dd4ebae0ccb77e5f7cad6cf984c5e64f8b4faa73`.

## Acquisition and fail-closed path

- Lock deliberately wrong mandate digest: `0x5a17dce794c7c215f611faf9c48bcdb15a3addfe1406d30d49aa92f5c3d9c2f2`
- Assess fetched bytes: `0x5ee881b80035a5fd4fa00b7922491cb2aa116c0c1ada4793cd8fe20e65edbbbb`
- Readback: `UNRESOLVED`, reason `DIGEST_MISMATCH`, `ticket_used=false`, nonce `0`.

## Material-drift path

- Lock hidden-admin bundle: `0x13f543d2a9dd675484f4a10fb56ad578a2bc39509e18e43dbf72a6d24e11e860`
- Initial assessment consensus rollback: `0xa6990f3d9119b874c801e479054b72c99528723727baf8da8cd9605ddfe9e30a` (`MAJORITY_DISAGREE`; state remained `PENDING`).
- Safe retry of the same revision: `0x9c66215dc164072788b36cf32dda689551770ca37c47a1cfb1b63ef17644e362`
- Readback: `MATERIAL_DRIFT`; the hidden admin grant produced `material_drift=true` and no execution authority.
- Bound executor attempts to consume the negative verdict: `0x34c412e7166fa5d5c4608197f898be0dfa268940babf41147c25dba562dd60e4`
- Complete proposal state before and after the rejected consume was equal.

## Recovery and positive path

- Lock the canonical evidence pair as revision 3: `0x80e3a5a2270dd0570e0e668b9dc4948792964515c145b6c8da7754c06a2bc700`
- Assess canonical evidence: `0xa1390afd86103163dabcb9b4a82ea2159c32ce0ccf09b3de0eac8df858beab01`
- Readback: `ALIGNED`; every mandatory positive predicate is true, `material_drift=false`, receipt `7158118cc2f2c991495e346ad6e7db6fb18fce30e287d342010c953e5db6c16d`.

## Authorization and replay matrix

- Governance wallet tries executor-only consume: `0x6d8041a114ae2f980bd421532890adec663e2e667b156f4f4d14d6c7f5f82618`
- Executor supplies stale revision: `0xffec3590efaf8ebde06fec053ad11209cacfd680b4627ef98ccc237d9c31ddec`
- Executor supplies changed bundle digest: `0x1302bc5dfd234cdfab84b59e2607a87d8cd065645553b58f51b69c769cd64e31`
- Each rejected sequence preserved the complete ALIGNED state, `ticket_used=false`, nonce `0`.
- Bound executor consumes the exact current ticket: `0x828bd680c13e2c42cf91eef7d37f23ef98db1d21eb1030de2809a3fa6ce32c1c`
- Readback: `CONSUMED`, `ticket_used=true`, nonce `1`.
- Exact replay attempt: `0x898ad7a0c78e33b3c23257302164e505b54748442a35bd95e69c8cb7ae854f41`
- Terminal readback remained exactly `CONSUMED`, `ticket_used=true`, nonce `1`.

All listed writes reached `FINALIZED`. Contract-error transactions show `MAJORITY_AGREE` because validators agreed on the deterministic rollback; success is established only by the leader execution result and the authoritative post-state readback.
