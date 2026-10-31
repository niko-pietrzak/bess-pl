"""Raw snapshots: responses stored exactly as received, before each gate closure.

Standard library only, so the same code runs on the Mac (launchd) and in the cloud.
Raw bytes are never parsed here (stage 4); the only peek is PSE `nextLink` for paging.
"""

import hashlib
import json
import os
import ssl
import subprocess
import time as time_module
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import certifi

from bess.ingest.datasets import WARSAW, Request, requests_for

# Information cutoffs per slot, local time on D-1 (ADR-0006). `poll` has no cutoff (O6).
CUTOFFS = {"reserves": time(8, 30), "dayahead": time(11, 0), "poll": None}
SAFETY = timedelta(minutes=5)  # stop retrying this long before the cutoff
LATE_RUN_RETRY_WINDOW = timedelta(minutes=10)
TIMEOUT_S = 60
MAX_PAGES = 50
KEPT_HEADERS = ("content-type", "content-length", "last-modified", "etag", "date")

Opener = Callable[..., object]


def redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    return text


class LocalStore:
    """Write-once file store; `put` refuses to overwrite (data/raw is immutable)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def put(self, key: str, data: bytes) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as f:
            f.write(data)


@dataclass
class Response:
    status: int | None
    headers: dict[str, str]
    body: bytes
    error: str | None = None


@dataclass
class Report:
    slot: str
    run_dir: str
    critical_failures: list[str] = field(default_factory=list)
    other_failures: list[str] = field(default_factory=list)
    files: int = 0

    @property
    def ok(self) -> bool:
        return not self.critical_failures


def cutoff_utc(slot: str, run_date: date) -> datetime | None:
    local = CUTOFFS[slot]
    if local is None:
        return None
    return datetime.combine(run_date, local, tzinfo=WARSAW).astimezone(UTC)


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _extension(content_type: str) -> str:
    for marker, ext in (("json", "json"), ("xml", "xml"), ("zip", "zip")):
        if marker in content_type:
            return ext
    return "bin"


def _code_version() -> str | None:
    if os.environ.get("BESS_CODE_VERSION"):
        return os.environ["BESS_CODE_VERSION"]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def default_opener(req: urllib.request.Request, timeout: float):
    """urlopen with Mozilla's CA bundle: macOS /etc/ssl/cert.pem lacks the root PSE uses."""
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)


_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def http_get(url: str, opener: Opener) -> Response:
    req = urllib.request.Request(url, headers={"User-Agent": "bess-pl snapshot"})
    try:
        with opener(req, timeout=TIMEOUT_S) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return Response(resp.status, headers, resp.read())
    except urllib.error.HTTPError as e:
        headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        return Response(e.code, headers, e.read() or b"", error=f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Response(None, {}, b"", error=f"{type(e).__name__}: {e}")


def _retryable(r: Response) -> bool:
    return r.status is None or r.status == 429 or r.status >= 500


@dataclass
class _Item:
    """One HTTP call still to be made: a request, or a further page of one."""

    req: Request
    url: str
    page: int = 1
    attempts: list[dict] = field(default_factory=list)
    started: datetime | None = None


def run_slot(
    slot: str,
    store: LocalStore,
    token: str | None,
    opener: Opener = default_opener,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time_module.sleep,
    requests: list[Request] | None = None,
    log: Callable[[str], None] = print,
) -> Report:
    """Download every request of one slot into snapshots/<run_date>/<slot>/<run_id>/.

    Retries go in rounds: each round tries every pending call once, then waits with
    exponential backoff, until the deadline (cutoff minus SAFETY). One dead endpoint
    therefore cannot use up the retry window of the others.
    """
    secrets = [token] if token else []
    started = now()
    run_date = started.astimezone(WARSAW).date()
    cutoff = cutoff_utc(slot, run_date)
    deadline = started + LATE_RUN_RETRY_WINDOW
    if cutoff:
        deadline = max(cutoff - SAFETY, deadline)
    run_dir = f"snapshots/{run_date}/{slot}/{started:%Y%m%dT%H%M%SZ}"
    report = Report(slot, run_dir)
    version = _code_version()

    def save(item: _Item, r: Response, finished: datetime) -> None:
        req = item.req
        suffix = f"__p{item.page}" if item.page > 1 else ""
        key = f"{run_dir}/{_name(req)}{suffix}"
        ext = _extension(r.headers.get("content-type", ""))
        meta = {
            "source": req.source,
            "dataset": req.dataset,
            "part": req.part,
            "page": item.page,
            "url": redact(item.url, secrets),
            "critical": req.critical,
            "slot": slot,
            "run_date": str(run_date),
            "vintage": "poll" if cutoff is None else "cutoff-snapshot",
            "cutoff_utc": _iso(cutoff) if cutoff else None,
            "fetch_started_utc": _iso(item.started),
            "fetch_finished_utc": _iso(finished),
            "valid_for_cutoff": (finished < cutoff) if cutoff else None,
            "http_status": r.status,
            "headers": {k: v for k, v in r.headers.items() if k in KEPT_HEADERS},
            "sha256": hashlib.sha256(r.body).hexdigest(),
            "size": len(r.body),
            "file": f"{key.rsplit('/', 1)[-1]}.{ext}",
            "attempts": item.attempts,
            "code_version": version,
        }
        store.put(f"{key}.{ext}", r.body)
        store.put(f"{key}.meta.json", json.dumps(meta, indent=1).encode())
        report.files += 1

    pending: list[_Item] = []
    for req in requests if requests is not None else requests_for(run_date):
        if req.needs_token and not token:
            _fail(report, req, f"{_name(req)}: ENTSOE_TOKEN not set", log)
            continue
        pending.append(_Item(req, req.url + (f"&securityToken={token}" if req.needs_token else "")))

    delay = 5.0
    while pending:
        retry: list[_Item] = []
        queue = list(pending)
        while queue:
            item = queue.pop(0)
            t0 = now()
            item.started = item.started or t0
            r = http_get(item.url, opener)
            item.attempts.append(
                {
                    "started_utc": _iso(t0),
                    "status": r.status,
                    "error": redact(r.error, secrets) if r.error else None,
                }
            )
            if _retryable(r) and now() + timedelta(seconds=delay) < deadline:
                retry.append(item)
                continue
            save(item, r, now())
            if r.status != 200:
                detail = redact(f"{_name(item.req)}: {r.error or f'HTTP {r.status}'}", secrets)
                _fail(report, item.req, detail, log)
                continue
            next_url = _next_link(item.req, r)
            if next_url and item.page < MAX_PAGES:
                queue.insert(0, _Item(item.req, next_url, item.page + 1))
        if retry:
            sleep(delay)
            delay = min(delay * 2, 60.0)
        pending = retry

    finished = now()
    summary = {
        "slot": slot,
        "run_date": str(run_date),
        "cutoff_utc": _iso(cutoff) if cutoff else None,
        "started_utc": _iso(started),
        "finished_utc": _iso(finished),
        "files": report.files,
        "critical_failures": report.critical_failures,
        "other_failures": report.other_failures,
        "code_version": version,
    }
    store.put(f"{run_dir}/_run.json", json.dumps(summary, indent=1).encode())
    log(
        f"{slot} {run_date}: {report.files} files, "
        f"{len(report.critical_failures)} critical and {len(report.other_failures)} other failures"
    )
    return report


def _name(req: Request) -> str:
    return f"{req.source}/{req.dataset}" + (f"__{req.part}" if req.part else "")


def _fail(report: Report, req: Request, message: str, log: Callable[[str], None]) -> None:
    (report.critical_failures if req.critical else report.other_failures).append(message)
    log(("CRITICAL " if req.critical else "") + message)


def _next_link(req: Request, r: Response) -> str | None:
    if req.source != "pse":
        return None
    try:
        return json.loads(r.body).get("nextLink")
    except (ValueError, AttributeError):
        return None


def ping(url: str | None, report: Report, secrets: list[str], opener: Opener) -> None:
    """Healthchecks: success ping only after a full run; /fail with the critical errors."""
    if not url:
        return
    if report.ok:
        req = urllib.request.Request(url)
    else:
        body = redact("\n".join([report.run_dir, *report.critical_failures]), secrets)
        req = urllib.request.Request(f"{url.rstrip('/')}/fail", data=body.encode(), method="POST")
    try:
        with opener(req, timeout=15):
            pass
    except (urllib.error.URLError, TimeoutError, OSError):
        pass  # healthchecks raises the alarm itself when no ping arrives
