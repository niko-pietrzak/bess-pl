import hashlib
import io
import json
import urllib.error
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from email.message import Message

import pytest

from bess.ingest.datasets import Request, local_day_start_utc, requests_for
from bess.ingest.snapshot import LocalStore, Report, cutoff_utc, ping, run_slot
from bess.ingest.timestamp import Stamp

TOKEN = "s3cr3t-token-value"


class FakeClock:
    def __init__(self, start: datetime):
        self.t = start

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += timedelta(seconds=seconds)


class FakeResponse:
    def __init__(self, status: int, body: bytes, content_type: str = "application/json"):
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_from(responses):
    """Each call pops the next item: a FakeResponse, an int (HTTP error) or an exception."""
    calls = []

    def opener(req, timeout):
        calls.append(req)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, int):
            raise urllib.error.HTTPError(req.full_url, item, "err", Message(), io.BytesIO(b"x"))
        return item

    opener.calls = calls
    return opener


def recorder(sent):
    def opener(req, timeout):
        sent.append(req)
        return FakeResponse(200, b"OK")

    return opener


def stamper_at(clock, granted=2):
    def stamper(data):
        return [
            Stamp(
                name,
                "http://tsa",
                i < granted,
                None if i < granted else "down",
                clock.now(),
                b"tsr",
                "pem",
            )
            for i, name in enumerate(["a", "b"])
        ]

    return stamper


def run(tmp_path, responses, requests, start, slot="reserves", token=TOKEN, granted=2):
    clock = FakeClock(start)
    opener = opener_from(responses)
    report = run_slot(
        slot,
        LocalStore(tmp_path),
        token,
        opener=opener,
        now=clock.now,
        sleep=clock.sleep,
        requests=requests,
        log=lambda _: None,
        stamper=stamper_at(clock, granted),
    )
    return report, opener


def metas(tmp_path):
    return [json.loads(p.read_text()) for p in sorted(tmp_path.rglob("*.meta.json"))]


PSE_REQ = Request("pse", "zmb", "", "https://api.raporty.pse.pl/api/zmb?x=1", critical=True)
ENTSOE_REQ = Request("entsoe", "load_forecast", "", "https://e.eu/api?a=1", True, needs_token=True)
# 07:00 UTC on 2 Nov 2026 = 08:00 CET, 30 minutes before the reserves cutoff
MORNING = datetime(2026, 11, 2, 7, 0, tzinfo=UTC)


def test_raw_bytes_and_meta_are_stored(tmp_path):
    body = b'{"value": [1, 2]}'
    report, _ = run(tmp_path, [FakeResponse(200, body)], [PSE_REQ], MORNING)
    assert report.ok and report.files == 1
    raw = next(tmp_path.rglob("zmb.json"))
    assert raw.read_bytes() == body
    (meta,) = metas(tmp_path)
    assert meta["sha256"] == hashlib.sha256(body).hexdigest()
    assert meta["http_status"] == 200
    assert meta["cutoff_utc"] == "2026-11-02T07:30:00.000Z"
    assert meta["valid_for_cutoff"] is True
    assert meta["vintage"] == "cutoff-snapshot"
    assert "snapshots/2026-11-02/reserves/20261102T070000Z/pse" in str(raw)
    assert (raw.parent.parent / "_run.json").exists()


def test_store_never_overwrites(tmp_path):
    store = LocalStore(tmp_path)
    store.put("a/b.json", b"1")
    with pytest.raises(FileExistsError):
        store.put("a/b.json", b"2")


def test_retries_on_server_error_then_succeeds(tmp_path):
    report, opener = run(tmp_path, [503, 503, FakeResponse(200, b"{}")], [PSE_REQ], MORNING)
    assert report.ok
    assert len(opener.calls) == 3
    assert [a["status"] for a in metas(tmp_path)[0]["attempts"]] == [503, 503, 200]


def test_no_retry_on_client_error(tmp_path):
    report, opener = run(tmp_path, [400], [PSE_REQ], MORNING)
    assert len(opener.calls) == 1
    assert report.critical_failures == ["pse/zmb: HTTP 400"]


def test_retries_stop_before_cutoff(tmp_path):
    report, opener = run(tmp_path, [503] * 100, [PSE_REQ], MORNING)
    assert not report.ok
    (meta,) = metas(tmp_path)
    last_attempt = datetime.fromisoformat(meta["attempts"][-1]["started_utc"])
    assert last_attempt < datetime(2026, 11, 2, 7, 25, tzinfo=UTC)


def test_late_run_is_marked_invalid(tmp_path):
    late = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)  # 09:00 CET, after the 08:30 cutoff
    run(tmp_path, [FakeResponse(200, b"{}")], [PSE_REQ], late)
    assert metas(tmp_path)[0]["valid_for_cutoff"] is False


def test_pse_next_link_is_followed(tmp_path):
    page1 = json.dumps({"value": [1], "nextLink": "https://api.raporty.pse.pl/api/zmb?p=2"})
    responses = [FakeResponse(200, page1.encode()), FakeResponse(200, b'{"value": [2]}')]
    report, opener = run(tmp_path, responses, [PSE_REQ], MORNING)
    assert report.files == 2
    assert opener.calls[1].full_url.endswith("p=2")
    assert next(tmp_path.rglob("zmb__p2.json")).read_bytes() == b'{"value": [2]}'


def test_token_never_written_or_reported(tmp_path):
    leak = urllib.error.URLError(f"failed https://e.eu/api?a=1&securityToken={TOKEN}")
    responses = [FakeResponse(200, b"<xml/>", "text/xml")] + [leak] * 100
    report, opener = run(tmp_path, responses, [ENTSOE_REQ, replace(ENTSOE_REQ, part="b")], MORNING)
    assert TOKEN in opener.calls[0].full_url  # sent to the API ...
    for path in tmp_path.rglob("*"):  # ... but never stored
        if path.is_file():
            assert TOKEN not in path.read_text(errors="ignore")
    assert all(TOKEN not in m for m in report.critical_failures)
    sent = []
    ping("https://hc.example/abc", report, [TOKEN], recorder(sent))
    assert sent[0].full_url == "https://hc.example/abc/fail"
    assert TOKEN not in sent[0].data.decode()
    assert "***" in sent[0].data.decode()


def test_missing_token_is_a_failure_without_request(tmp_path):
    report, opener = run(tmp_path, [], [ENTSOE_REQ], MORNING, token=None)
    assert opener.calls == []
    assert report.critical_failures == ["entsoe/load_forecast: ENTSOE_TOKEN not set"]


def test_ping_success_only_when_no_critical_failure():
    sent = []
    report = Report("reserves", "d", other_failures=["x"])
    ping("https://hc.example/abc", report, [], recorder(sent))
    assert sent[0].full_url == "https://hc.example/abc"
    assert sent[0].data is None


@pytest.mark.parametrize(
    "slot, day, expected_utc",
    [
        ("reserves", date(2026, 11, 2), datetime(2026, 11, 2, 7, 30, tzinfo=UTC)),  # CET
        ("reserves", date(2027, 3, 28), datetime(2027, 3, 28, 6, 30, tzinfo=UTC)),  # 23-h day
        ("dayahead", date(2027, 3, 28), datetime(2027, 3, 28, 9, 0, tzinfo=UTC)),
        ("dayahead", date(2027, 10, 31), datetime(2027, 10, 31, 10, 0, tzinfo=UTC)),  # 25-h day
        ("poll", date(2027, 10, 31), None),
    ],
)
def test_cutoff_in_utc_across_dst(slot, day, expected_utc):
    assert cutoff_utc(slot, day) == expected_utc


def test_local_day_boundaries_across_dst():
    assert local_day_start_utc(date(2027, 3, 28)) == datetime(2027, 3, 27, 23, 0, tzinfo=UTC)
    assert local_day_start_utc(date(2027, 3, 29)) == datetime(2027, 3, 28, 22, 0, tzinfo=UTC)


def test_catalogue():
    reqs = requests_for(date(2026, 11, 2))
    critical = {(r.source, r.dataset) for r in reqs if r.critical}
    assert {("pse", "zmb"), ("pse", "pdgopkd"), ("entsoe", "day_ahead_prices")} <= critical
    assert all("securityToken" not in r.url for r in reqs)
    assert all(r.needs_token for r in reqs if r.source == "entsoe")
    names = [(r.source, r.dataset, r.part) for r in reqs]
    assert len(names) == len(set(names))
    pse = next(r for r in reqs if r.dataset == "zmb")
    assert "2026-11-02" in pse.url and "2026-11-03" in pse.url


def test_dead_endpoint_does_not_starve_others(tmp_path):
    dead = Request("pse", "dead", "", "https://api.raporty.pse.pl/api/dead", critical=True)
    flaky_calls = []

    def opener(req, timeout):
        if "dead" in req.full_url:
            raise urllib.error.URLError("down")
        flaky_calls.append(req)
        if len(flaky_calls) < 4:
            raise urllib.error.HTTPError(req.full_url, 503, "err", Message(), io.BytesIO(b""))
        return FakeResponse(200, b"{}")

    clock = FakeClock(MORNING)
    report = run_slot(
        "reserves",
        LocalStore(tmp_path),
        None,
        opener=opener,
        now=clock.now,
        sleep=clock.sleep,
        requests=[dead, PSE_REQ],
        log=lambda _: None,
        stamper=stamper_at(clock),
    )
    assert report.critical_failures == ["pse/dead: URLError: <urlopen error down>"]
    assert len(flaky_calls) == 4
    assert {m["dataset"]: m["http_status"] for m in metas(tmp_path)} == {"dead": None, "zmb": 200}


def test_manifest_lists_every_file_and_is_sealed(tmp_path):
    report, _ = run(tmp_path, [FakeResponse(200, b"{}")], [PSE_REQ], MORNING)
    run_dir = tmp_path / report.run_dir
    manifest = json.loads((run_dir / "_manifest.json").read_text())
    listed = {f["path"]: f["sha256"] for f in manifest["files"]}
    assert set(listed) == {"pse/zmb.json", "pse/zmb.meta.json", "_run.json"}
    for path, digest in listed.items():
        assert hashlib.sha256((run_dir / path).read_bytes()).hexdigest() == digest
    assert (run_dir / "_manifest.a.tsr").exists() and (run_dir / "_manifest.b.chain.pem").exists()
    assert json.loads((run_dir / "_tsa.json").read_text())["valid_for_cutoff"] is True


def test_late_time_stamp_is_critical(tmp_path):
    late = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
    report, _ = run(tmp_path, [FakeResponse(200, b"{}")], [PSE_REQ], late)
    assert report.critical_failures[-1].startswith("late: time stamp 2026-11-02T08:00")
    tsa = json.loads((tmp_path / report.run_dir / "_tsa.json").read_text())
    assert tsa["valid_for_cutoff"] is False


def test_one_token_is_not_enough(tmp_path):
    report, _ = run(tmp_path, [FakeResponse(200, b"{}")], [PSE_REQ], MORNING, granted=1)
    assert report.critical_failures == ["time stamp: 1 of 2 tokens (b: down)"]


def test_poll_has_manifest_without_time_stamp(tmp_path):
    report, _ = run(tmp_path, [FakeResponse(200, b"{}")], [PSE_REQ], MORNING, slot="poll")
    assert report.ok
    assert (tmp_path / report.run_dir / "_manifest.json").exists()
    assert not (tmp_path / report.run_dir / "_tsa.json").exists()
