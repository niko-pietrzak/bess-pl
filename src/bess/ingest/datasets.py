"""Catalogue of datasets snapshotted before each gate closure (ADR-0006).

One `Request` per HTTP call. Windows are in local delivery days relative to the run date T
(the snapshot runs on D-1, so T = D-1). Why each dataset is snapshotted: docs/data-sources.md.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

PSE_API = "https://api.raporty.pse.pl/api/"
ENTSOE_API = "https://web-api.tp.entsoe.eu/api"
OPEN_METEO_SINGLE_RUNS = "https://single-runs-api.open-meteo.com/v1/forecast"

PL = "10YPL-AREA-----S"
NEIGHBOURS = {
    "DE_LU": "10Y1001A1001A82H",
    "CZ": "10YCZ-CEPS-----N",
    "SK": "10YSK-SEPS-----K",
    "LT": "10YLT-1001A0008Q",
    "SE_4": "10Y1001A1001A47J",
}


@dataclass(frozen=True)
class Request:
    source: str
    dataset: str
    part: str
    url: str  # full URL without secrets; the ENTSO-E token is added at fetch time
    critical: bool
    needs_token: bool = False


# fmt: off
# PSE API v2 endpoints: (endpoint, first day, last day relative to T, critical).
PSE_DATASETS = [
    ("zmb", 0, 1, True),  # RMB capacity demand, by 07:30 D-1
    ("cmbp-tp", -1, 1, True),  # RMB capacity prices
    ("kse-load", 0, 2, True),  # load forecast
    ("price-fcst", 0, 1, True),  # forecast CEN, CKOEB, CEB
    ("csdac-pln", -1, 1, True),  # SDAC price in PLN
    ("pdgopkd", 0, 1, True),  # daily coordination plan (PKD)
    ("pdgobpkd", 0, 1, True),  # current daily coordination plan (BPKD)
    ("pk5l-wp", 0, 12, True),  # coordination plan: wind, PV, demand forecast, surplus, D..D+11
    ("mbp-tp", -1, 1, False),
    ("cmbu-tu", -1, 1, False),
    ("mbu-tu", -1, 1, False),
    ("crb-rozl", -7, 0, False),
    ("sk", -1, 1, False),
    ("ro-prog", 0, 1, False),
    ("cordmax", 0, 1, False),
    ("rce-pln", -1, 1, False),
    ("energy-prices", -1, 0, False),
    ("popmb-rmb", -1, 1, False),
    ("pdgsz", 0, 1, False),
    ("pdwkseub", 0, 1, False),
    ("ogr-d1", 0, 1, False),
    ("przeplywy-mocy", -1, 0, False),
    ("his-wlk-cal", -2, 0, False),
]

# ENTSO-E: (dataset, Transparency Regulation article, params, first day, last day, critical).
ENTSOE_DATASETS = [
    ("day_ahead_prices", "12.1.D",
     {"documentType": "A44", "in_Domain": PL, "out_Domain": PL,
      "contract_MarketAgreement.type": "A01"}, -1, 1, True),
    ("load_forecast", "6.1.B",
     {"documentType": "A65", "processType": "A01", "outBiddingZone_Domain": PL}, 0, 1, True),
    ("wind_solar_forecast", "14.1.D",
     {"documentType": "A69", "processType": "A01", "in_Domain": PL}, 0, 1, False),
    ("generation_forecast", "14.1.C",
     {"documentType": "A71", "processType": "A01", "in_Domain": PL}, 0, 1, False),
    ("contracted_reserves_fcr", "17.1.B/C",
     {"documentType": "A81", "businessType": "B95", "processType": "A52",
      "type_MarketAgreement.Type": "A01", "controlArea_Domain": PL}, -1, 1, False),
    ("contracted_reserves_afrr", "17.1.B/C",
     {"documentType": "A81", "businessType": "B95", "processType": "A51",
      "type_MarketAgreement.Type": "A01", "controlArea_Domain": PL}, -1, 1, False),
    ("procured_balancing_capacity_fcr", "EB 12.3.F",
     {"documentType": "A15", "processType": "A52", "area_Domain": PL}, -1, 1, False),
    ("procured_balancing_capacity_afrr", "EB 12.3.F",
     {"documentType": "A15", "processType": "A51", "area_Domain": PL}, -1, 1, False),
    ("activated_balancing_energy_prices", "17.1.F",
     {"documentType": "A84", "processType": "A16", "controlArea_Domain": PL}, -2, 0, False),
    ("imbalance_prices", "17.1.G",
     {"documentType": "A85", "controlArea_Domain": PL}, -2, 0, False),
    ("imbalance_volumes", "17.1.H",
     {"documentType": "A86", "controlArea_Domain": PL}, -2, 0, False),
]
for _name in ("DE_LU", "CZ", "LT"):
    ENTSOE_DATASETS.append(
        (f"wind_solar_forecast__{_name}", "14.1.D",
         {"documentType": "A69", "processType": "A01", "in_Domain": NEIGHBOURS[_name]},
         0, 1, False)
    )
ENTSOE_DATASETS.append(
    ("load_forecast__DE_LU", "6.1.B",
     {"documentType": "A65", "processType": "A01",
      "outBiddingZone_Domain": NEIGHBOURS["DE_LU"]}, 0, 1, False)
)
for _name, _code in NEIGHBOURS.items():
    for _a, _b, _dir in ((PL, _code, f"PL-{_name}"), (_code, PL, f"{_name}-PL")):
        ENTSOE_DATASETS += [
            (f"physical_flows__{_dir}", "12.1.G",
             {"documentType": "A11", "out_Domain": _a, "in_Domain": _b}, -2, 0, False),
            (f"ntc_day_ahead__{_dir}", "11.1.A",
             {"documentType": "A61", "contract_MarketAgreement.Type": "A01",
              "out_Domain": _a, "in_Domain": _b}, 0, 1, False),
            (f"scheduled_exchanges_day_ahead__{_dir}", "12.1.F",
             {"documentType": "A09", "contract_MarketAgreement.Type": "A01",
              "out_Domain": _a, "in_Domain": _b}, -1, 1, False),
        ]

# Open-Meteo Single Runs. Points and variables are provisional; stage 10 decides.
WEATHER_POINTS = [
    ("PL", 52.23, 21.01), ("PL", 54.35, 18.65), ("PL", 54.19, 16.17), ("PL", 53.43, 14.55),
    ("PL", 52.41, 16.93), ("PL", 51.11, 17.03), ("PL", 50.26, 19.02), ("PL", 50.04, 22.00),
    ("PL", 53.13, 23.16), ("PL", 51.76, 19.46),
    ("DE", 53.55, 9.99), ("DE", 52.52, 13.41), ("DE", 50.94, 6.96), ("DE", 48.14, 11.58),
    ("DE", 54.48, 9.05),
    ("CZ", 50.08, 14.44), ("CZ", 49.20, 16.61),
    ("LT", 54.69, 25.28), ("LT", 55.70, 21.14),
]
WEATHER_VARIABLES = [
    "temperature_2m", "wind_speed_10m", "wind_speed_100m", "wind_direction_100m",
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation", "cloud_cover",
    "precipitation", "pressure_msl",
]
WEATHER_MODELS = ["ecmwf_ifs", "ecmwf_ifs025"]
# fmt: on


def local_day_start_utc(day: date) -> datetime:
    """Start of a local (Europe/Warsaw) day in UTC."""
    return datetime.combine(day, time(0), tzinfo=WARSAW).astimezone(UTC)


def _pse(endpoint: str, first: date, last: date, critical: bool) -> Request:
    query = urlencode(
        {
            "$filter": f"business_date ge '{first}' and business_date le '{last}'",
            "$first": "20000",
        }
    )
    return Request("pse", endpoint, "", f"{PSE_API}{endpoint}?{query}", critical)


def _entsoe(name: str, params: dict[str, str], first: date, last: date, critical: bool):
    dataset, _, part = name.partition("__")
    window = {
        "periodStart": local_day_start_utc(first).strftime("%Y%m%d%H%M"),
        "periodEnd": local_day_start_utc(last + timedelta(days=1)).strftime("%Y%m%d%H%M"),
    }
    url = f"{ENTSOE_API}?{urlencode(params | window)}"
    return Request("entsoe", dataset, part, url, critical, needs_token=True)


def _weather(model: str, run: datetime) -> Request:
    query = urlencode(
        {
            "latitude": ",".join(f"{lat}" for _, lat, _ in WEATHER_POINTS),
            "longitude": ",".join(f"{lon}" for _, _, lon in WEATHER_POINTS),
            "hourly": ",".join(WEATHER_VARIABLES),
            "models": model,
            "run": run.strftime("%Y-%m-%dT%H:%M"),
            "forecast_days": "4",
        }
    )
    part = f"{model}__run{run:%Y%m%dT%H}Z"
    return Request("open-meteo", "single_runs", part, f"{OPEN_METEO_SINGLE_RUNS}?{query}", False)


def requests_for(run_date: date) -> list[Request]:
    """All requests of one snapshot run on local date T = run_date."""
    days = lambda a, b: (run_date + timedelta(days=a), run_date + timedelta(days=b))  # noqa: E731
    out = [_pse(ep, *days(a, b), critical) for ep, a, b, critical in PSE_DATASETS]
    out += [
        _entsoe(name, params, *days(a, b), critical)
        for name, _article, params, a, b, critical in ENTSOE_DATASETS
    ]
    run_00 = datetime.combine(run_date, time(0), tzinfo=UTC)
    for model in WEATHER_MODELS:
        out += [_weather(model, run_00 - timedelta(hours=6)), _weather(model, run_00)]
    return out
