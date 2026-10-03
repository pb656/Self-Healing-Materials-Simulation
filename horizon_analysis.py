"""Compare finite-cycle break-even penalties with analytical limits.

Place beside simulation.py and run: python horizon_analysis.py
Uses only the Python standard library. Existing result files are not changed.
All inputs remain illustrative assumptions, not measured material properties.
"""
import csv
import json
import math
from pathlib import Path

from simulation import simulate

OUT = Path(__file__).resolve().parent / 'results'
SETTINGS = dict(d=0.03, r=0.75, h0=0.80, E=1.0, q=0.95)
HORIZONS = (10, 50, 100)


def log_gain(mode, N, *, d, r, h0, E, q):
    """Log strength ratio to the reference, before any initial penalty."""
    if mode not in ('sustained', 'declining'):
        raise ValueError('Unknown healing case')
    if not isinstance(N, int) or N < 1:
        raise ValueError('N must be a positive integer')
    if not 0 <= d < 1 or not all(0 <= x <= 1 for x in (r, h0, E, q)):
        raise ValueError('Ratio calculation requires d < 1 and bounded factors')
    c = d * r * h0 * E / (1 - d)
    if mode == 'sustained':
        return N * math.log1p(c)
    return math.fsum(math.log1p(c * q**k) for k in range(N))


def declining_limit(*, d, r, h0, E, q, tolerance=1e-14):
    """Bound the infinite-product result using log(1+x) <= x.

    After m factors, the omitted log sum is at most c*q**m/(1-q).
    This bounds numerical truncation, not physical prediction uncertainty.
    """
    if not 0 <= q < 1 or not 0 <= d < 1:
        raise ValueError('Requires q < 1 and d < 1')
    c = d * r * h0 * E / (1 - d)
    terms = []
    m = 0
    while c * q**m / (1 - q) > tolerance:
        terms.append(math.log1p(c * q**m))
        m += 1
    lower_log = math.fsum(terms)
    tail_bound = c * q**m / (1 - q)
    return dict(
        penalty_fraction_lower=-math.expm1(-lower_log),
        penalty_fraction_upper=-math.expm1(-(lower_log + tail_bound)),
        terms=m,
        omitted_log_sum_upper_bound=tail_bound,
    )


def main():
    rows = []
    for N in HORIZONS:
        for mode in ('sustained', 'declining'):
            gain = log_gain(mode, N, **SETTINGS)
            limit = -math.expm1(-gain)
            reference = simulate('reference', N=N, p=0, **SETTINGS)[-1]
            zero_penalty = simulate(mode, N=N, p=0, **SETTINGS)[-1]
            assert math.isclose(limit, 1 - reference / zero_penalty,
                                rel_tol=1e-12, abs_tol=1e-12)
            equal = simulate(mode, N=N, p=limit, **SETTINGS)[-1]
            assert math.isclose(equal, reference, rel_tol=1e-12, abs_tol=1e-12)
            for offset in (-0.001, 0.001):
                strength = simulate(mode, N=N, p=limit + offset, **SETTINGS)[-1]
                assert (strength > reference) == (offset < 0)
            rows.append(dict(cycles=N, case=mode,
                             equality_penalty_fraction=limit,
                             equality_penalty_percent=100 * limit))

    # q=1 makes the declining expression equal to sustained healing;
    # zero healing gives zero offsettable penalty.
    for N in HORIZONS:
        assert math.isclose(log_gain('declining', N, **{**SETTINGS, 'q': 1}),
                            log_gain('sustained', N, **SETTINGS), abs_tol=1e-12)
        assert log_gain('declining', N, **{**SETTINGS, 'E': 0}) == 0

    bound = declining_limit(**SETTINGS)
    for row in rows:
        if row['case'] == 'declining':
            assert row['equality_penalty_fraction'] < bound['penalty_fraction_upper']
    report = dict(settings=SETTINGS, horizons=list(HORIZONS),
                  declining_infinite_horizon=bound,
                  sustained_infinite_horizon_penalty_supremum=1.0,
                  interpretation='Equality with the damaged reference, not a design allowable',
                  input_status='Illustrative assumptions; not experimentally calibrated')
    OUT.mkdir(exist_ok=True)
    with (OUT / 'horizon_summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / 'horizon_settings.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for row in rows:
        print(f"{row['cycles']:3d} cycles | {row['case']:9s} | {row['equality_penalty_percent']:.2f}%")
    print(f"Declining infinite-horizon penalty limit: {100*bound['penalty_fraction_lower']:.4f}%")
    print('All six horizon cases and analytical checks passed.')


if __name__ == '__main__':
    main()
