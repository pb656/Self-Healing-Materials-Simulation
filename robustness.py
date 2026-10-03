"""Joint sensitivity and break-even analysis; all inputs remain assumed.
Run: python robustness.py. Uses only the Python standard library.
"""
from pathlib import Path
import csv
import json
import math
from simulation import BASE, simulate, verify

OUT = Path(__file__).resolve().parent / 'results'

def penalty_limit(mode, E, q):
    args = {**BASE, 'E': E, 'q': q, 'p': 0.}
    reference = simulate('reference', **args)[-1]
    gain = simulate(mode, **args)[-1]
    return 1-reference/gain

def threshold(mode, q=.95, p=.05):
    if penalty_limit(mode, 1., q) < p:
        return None
    lo, hi = 0., 1.
    for _ in range(60):
        mid = (lo+hi)/2
        if penalty_limit(mode, mid, q) < p:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

def main():
    verify()
    OUT.mkdir(exist_ok=True)
    rows = []
    for mode in ('sustained', 'declining'):
        for i in range(101):
            E = i/100
            for j in range(101):
                q = .90+.10*j/100
                args = {**BASE, 'E': E, 'q': q}
                reference = simulate('reference', **args)[-1]
                healed = simulate(mode, **args)[-1]
                limit = penalty_limit(mode, E, q)
                assert math.isclose(simulate(mode, **{**args, 'p': limit})[-1], reference, abs_tol=1e-12)
                rows.append(dict(case=mode, E=E, q=q, P50=healed,
                    advantage_percentage_points=100*(healed-reference),
                    maximum_penalty_for_equality=limit))
    with (OUT/'joint_sensitivity.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for mode in ('sustained', 'declining'):
        summary[mode] = dict(minimum_E_for_break_even_at_cycle_50=threshold(mode),
            maximum_penalty_at_E1=penalty_limit(mode, 1., .95),
            maximum_penalty_at_E05=penalty_limit(mode, .5, .95))
    (OUT/'break_even.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f'{len(rows)} joint cases and analytic boundary checks passed.')

if __name__ == '__main__':
    main()
