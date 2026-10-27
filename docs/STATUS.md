# Status · 2026-10-28

Stage 2 done. Next: stage 3 (ingest and raw snapshots).

Done
- Stages 0–1: ADR-0001 to 0004, primer, roadmap, repo skeleton, CLI.
- Stage 2: ADR-0005 data sources, ADR-0006 gate closures (from WDB), ADR-0003 amended; `docs/data-sources.md` with a role per dataset; glossary extended.

Next
1. Stage 3, first the daily 08:30 and 10:30 snapshots: every day without them loses forecast versions for good. Then backfill.
2. At the start of stage 3: Q5 (PL reserves on ENTSO-E) with the ENTSO-E token from `.env`.
3. Before publication #1: owner of PL day-ahead prices (O2a); questions to TGE (ADR-0005) and PSE (Q4, raporty.pse.pl terms), sent together.

Notes
- PSE `publication_ts` is the last revision time: own snapshots are the only proof of what was known at the cutoff.
