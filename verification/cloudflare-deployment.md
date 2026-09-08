# Cloudflare Pages deployment

- Production URL: `https://mandate-calldata-drift-guard.pages.dev/`
- Deployment URL: `https://f360963d.mandate-calldata-drift-guard.pages.dev/`
- Cloudflare project: `mandate-calldata-drift-guard`
- Production branch: `main`
- Upload result: 8 files uploaded successfully.
- Post-deployment HTTP check: production page returned `200`.
- Logo check: `/logo.png` returned `200` with `1,071,374` bytes.
- Bundle inspection: exact Studionet contract `0x3A0Bd8668420e5132B77c3626C9A1c2eac45Eeb6` is embedded through the production environment configuration.

The frontend reads and writes the deployed contract through `genlayer-js`; it does not maintain mock proposal state or generate fallback verdicts. The sentence displayed before a verified read explicitly states that no simulated verdict is loaded.
