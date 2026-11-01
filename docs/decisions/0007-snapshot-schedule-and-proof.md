# ADR-0007: Snapshot schedule, validity and proof

Status: proposed · 2026-11-01
Replaces the "08:30 and 10:30 snapshots" of ADR-0006 with the slots below; the cutoffs themselves (08:30 and 11:00 D-1) are unchanged.

## Context
PSE keeps only the last revision of each record and ENTSO-E overwrites forecasts (`docs/data-sources.md`), so our own snapshots are the only record of what was known at a cutoff. Requirements: no gaps, also during holidays; on time relative to the cutoff; Europe/Warsaw with daylight saving time (O1 in ADR-0006); an alert when a slot fails, because nobody checks daily; cost close to zero; little upkeep; secrets outside the repo; raw data private (ADR-0005). Since 1.11.2026 snapshots run on a Mac with launchd, which misses slots while the Mac sleeps.

## Decision
1. **Slots**, every day, Europe/Warsaw: `reserves` starts at 08:00 for the 08:30 cutoff, `dayahead` at 10:30 for the 11:00 cutoff. Retries run in rounds until cutoff − 5 min. A second invocation at 08:14 and 10:44 runs only if no valid sealed run exists yet for that slot (Lambda stops after 15 minutes). The measured publication times (O6) confirm or move these times.
2. **Validity:** a run is valid for its cutoff only if its manifest carries tokens from two independent Time Stamping Authorities (RFC 3161), both dated before the cutoff. Late or incomplete runs are kept and marked in `_tsa.json`, never used as the state at the cutoff. If both invocations fail, a catch-up run after the cutoff is stored as late.
3. **Proof:** `_manifest.json` lists SHA-256 and size of every file of the run. Tokens (DigiCert and Sectigo; GlobalSign and FreeTSA as fallbacks) and their certificate chains are stored next to it. Check: `openssl ts -verify -data _manifest.json -in _manifest.<tsa>.tsr -CAfile _manifest.<tsa>.chain.pem` (OpenSSL 3). A git commit date is not proof: it can be set freely.
4. **Where:** AWS eu-central-1. EventBridge Scheduler (cron in Europe/Warsaw, flexible window off) invokes a Lambda (Python 3.12) running the same `bess.ingest.snapshot` code, writing to a private S3 bucket with versioning; no Object Lock, no cross-region replication. The ENTSO-E token sits in SSM Parameter Store (SecureString). One template in `infra/`. A 5 USD budget with an e-mail alert exists before the first deployment.
5. **Alert:** healthchecks.io, one check per slot with a cron schedule in Europe/Warsaw. A success ping only after a full run (downloads, storage, two tokens); `/fail` with the list of critical failures otherwise. Critical datasets are marked in `docs/data-sources.md`; failures of the others go to the meta files and `bess status` only. No CloudWatch alarms.
6. **Copies:** S3 with versioning, plus a mirror on the Mac via `bess sync`. Raw data never enters the public repo.
7. **Later (stage 9):** a public repo `bess-pl-evidence` with daily manifests and tokens (no data), committed through the GitHub Contents API, and OpenTimestamps on each manifest as a long-term anchor that does not depend on TSA certificates. Public forecasts use the same mechanism.

Alternatives: GitHub Actions (its docs: scheduled runs "can be delayed during periods of high loads", "some queued jobs may be dropped", and schedules in public repos are disabled after 60 days without activity); Google Cloud Scheduler with Cloud Run (equivalent, no advantage); a VPS with systemd timers (punctual, but the operating system is ours to maintain); launchd on the Mac (interim only).

## Consequences
- EventBridge Scheduler evaluates cron in the IANA zone and adjusts for DST; 08:00 and 10:30 never fall into the 02:00–03:00 gap. DST days are covered by unit tests.
- Publication times are recorded in UTC. ECMWF and Open-Meteo follow UTC schedules, PSE local time, so in summer the UTC sources appear one hour later in local time: the measurement is repeated after 28.03.2027.
- Tokens rely on TSA certificates staying verifiable; OpenTimestamps (stage 9) removes that dependency.
- About 10 MB a day; Lambda, Scheduler and S3 cost cents a month at most. `certifi` must ship in the Lambda package.
