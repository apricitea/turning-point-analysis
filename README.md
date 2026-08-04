# turning-point-analysis

[![CI](https://github.com/apricitea/turning-point-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/apricitea/turning-point-analysis/actions/workflows/ci.yml)

Bull/bear market phase dating for IDX stocks, using a censored local-extrema
algorithm in the style of Pagan & Sossounov (2003) — the standard approach in
the finance literature for dating market cycles without relying on an
arbitrary fixed lookback window.

## Method

1. Find candidate turning points as local maxima/minima over a rolling
   window (`scipy.signal.argrelextrema`).
2. Enforce strict peak/trough alternation — if two peaks (or two troughs)
   occur back to back, keep only the more extreme one.
3. Censor phases that don't clear a minimum duration or minimum amplitude
   threshold, merging them into their neighbors. This is what separates a
   real market phase from short-lived noise.

See `turning_point_analysis/detector.py`. Correctness is checked in
`tests/test_detector.py` — alternation always holds, phases always span the
full series, and low-amplitude wiggles get censored out.

## Results — BBRI, 2020–2024

```
regime      start        end  duration_days  return_pct
  bear 2020-01-24 2020-05-18            115      -54.22
  bull 2020-05-18 2020-08-25             99       75.12
  bear 2020-08-25 2020-09-24             30      -20.26
  bull 2020-09-24 2021-01-20            118       61.39
  bear 2021-01-20 2021-07-30            191      -24.13
  bull 2021-07-30 2022-04-26            270       46.47
  bear 2022-04-26 2022-07-04             69      -18.22
  bull 2022-07-04 2023-08-10            402       41.09
  bear 2023-08-10 2023-11-01             83      -15.26
  bull 2023-11-01 2024-03-13            133       32.51
  bear 2024-03-13 2024-06-19             98      -35.94
  bull 2024-06-19 2024-09-24             97       34.76
  bear 2024-09-24 2024-09-30              6      -10.41
```

Bull phases: 6, avg duration 186d, avg return +48.6%. Bear phases: 7, avg
duration 85d, avg return -25.5%. The algorithm correctly isolates the
COVID crash (Jan–May 2020, -54%) as the first bear phase without being told
where to look.

## Usage

```bash
poetry install
poetry run python scripts/analyze.py
```

## Stack

Python · pandas · scipy · matplotlib
