# Status · 2026-11-01

Stage 3 in progress: steps 1, 1b and 2 done; ADR-0007 proposed, awaiting acceptance.

Done
- `bess snapshot --slot reserves|dayahead|poll`: raw responses with meta, retries until cutoff − 5 min, manifest with two RFC 3161 tokens per slot.
- Temporary schedule on the Mac (`deploy/launchd/install.sh`): 08:00 and 10:30 Europe/Warsaw from 1.11.2026.
- `docs/data-sources.md`: snapshot and critical columns; PSE v2 names; PKD and `pk5l-wp` added. Roadmap notes for stages 3, 6, 7, 10.

Next
1. Owner: `ENTSOE_TOKEN` and healthchecks ping URLs (`BESS_HC_RESERVES`, `BESS_HC_DAYAHEAD`) in `.env`; until then ENTSO-E fails every slot.
2. Accept ADR-0007, then add its note to ADR-0006; step 5: deploy to AWS (budget first), forced-failure alert test, remove launchd.
3. Step 6: publication-time polling for 14 days; step 7: backfill from 06.2024 and Q5; step 8: `bess status`.
