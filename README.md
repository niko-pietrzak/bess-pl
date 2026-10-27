# bess-pl

An open monthly revenue index for a 1 MW battery (2h and 4h) in Poland.

An independent referee: open method, two numbers, publicly scored forecasts.

- **Ceiling**: revenue with perfect foresight of all prices.
- **Realistic variant**: each market decision uses only information published before its gate closure.
- **Capture rate** = realistic / ceiling.

Markets in v1: day-ahead, FCR and aFRR capacity, aFRR energy. Unit: PLN/MW/year, gross.

## Status
Early development; first publication planned for January 2027. See [docs/STATUS.md](docs/STATUS.md) and [docs/roadmap.md](docs/roadmap.md).

## Run
Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run bess --help
```

## Read more
- [How a battery earns money in Poland](docs/market-primer.md)
- [Decisions (ADRs)](docs/decisions/)

## Licence
MIT, see [LICENSE](LICENSE).
