"""Illustrative self-healing model; all inputs are assumptions, not measured data.

Run: python simulation.py
Requires matplotlib for figures; calculations use only the standard library.
Outputs are written next to this script in results/.
"""
from pathlib import Path
import csv
import itertools
import json
import math

BASE = dict(N=50, d=0.03, r=0.75, p=0.05, h0=0.80, E=1.0, q=0.95)
MODES = ('reference', 'sustained', 'declining')
OUT = Path(__file__).resolve().parent / 'results'


def simulate(mode, N=50, d=.03, r=.75, p=.05, h0=.8, E=1., q=.95):
    """q is the retained availability per cycle, so A_n=q**(n-1).
    Reference always starts at 1 and has no healing. E affects healing only.
    """
    if mode not in MODES or not isinstance(N, int) or N < 1:
        raise ValueError('Invalid mode or cycle count')
    if not 0 <= p < 1 or not all(0 <= x <= 1 for x in (d, r, h0, E, q)):
        raise ValueError('Parameters outside their allowed bounds')
    values = [1. if mode == 'reference' else 1-p]
    for n in range(1, N+1):
        A = q**(n-1) if mode == 'declining' else 1.
        h = 0. if mode == 'reference' else h0*E*A
        previous = values[-1]
        damaged = previous*(1-d)
        healed = damaged + h*r*(previous-damaged)
        assert -1e-12 <= damaged <= healed+1e-12 <= previous+2e-12
        values.append(healed)
    return values


def verify():
    # Independent closed-form checks over boundary and intermediate parameters.
    for d, r, h0, E in itertools.product((0., .4, 1.), repeat=4):
        series = simulate('sustained', d=d, r=r, h0=h0, E=E)
        for n, value in enumerate(series):
            assert math.isclose(value, .95*(1-d*(1-h0*E*r))**n, abs_tol=1e-12)
    assert simulate('declining', d=0)[-1] == .95
    assert math.isclose(simulate('declining', h0=0)[-1], .95*.97**50)
    assert math.isclose(simulate('sustained', r=1, h0=1, E=1)[-1], .95)
    assert simulate('declining', q=1) == simulate('sustained')
    # With q=0, only the first cycle has healing availability.
    assert math.isclose(simulate('declining', q=0)[-1], .95*.988*.97**49)
    assert simulate('reference', d=1)[-1] == 0


def write_csv(name, rows):
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    verify()
    OUT.mkdir(exist_ok=True)
    trajectories, summary = [], []
    series = {}
    for E in (1., .5):
        reference = simulate('reference', **{**BASE, 'E': E})
        for mode in MODES:
            values = simulate(mode, **{**BASE, 'E': E})
            series[E, mode] = values
            crossing = next((n for n in range(1, 51) if values[n] > reference[n]+1e-12), None)
            summary.append(dict(E=E, case=mode, P50=values[-1], retained_percent=100*values[-1], first_exceeds_reference=crossing))
            trajectories.extend(dict(E=E, case=mode, cycle=n, P=value) for n, value in enumerate(values))
    write_csv('trajectories.csv', trajectories)
    write_csv('summary.csv', summary)
    # One-at-a-time, evenly spaced exploratory sweeps, holding other inputs fixed.
    ranges = {'d': (.01, .05), 'r': (0., 1.), 'p': (0., .15),
              'h0': (0., 1.), 'E': (0., 1.), 'q': (.90, 1.)}
    sensitivity = []
    for parameter, (lo, hi) in ranges.items():
        for i in range(101):
            x = lo+(hi-lo)*i/100
            for mode in MODES:
                value = simulate(mode, **{**BASE, parameter: x})[-1]
                sensitivity.append(dict(parameter=parameter, value=x, case=mode, P50=value))
    write_csv('sensitivity.csv', sensitivity)
    (OUT/'settings.json').write_text(json.dumps(dict(baseline=BASE, E_cases=[1., .5], sensitivity_ranges=ranges,
        points_per_range=101, method='one-at-a-time', input_status='illustrative assumptions'), indent=2))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    colors = {'reference': '#666666', 'sustained': '#0072B2', 'declining': '#D55E00'}
    labels = {'reference': 'Without healing', 'sustained': 'Sustained healing', 'declining': 'Declining healing'}
    styles = {'reference': ':', 'sustained': '-', 'declining': '--'}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True, layout='constrained')
    for ax, E in zip(axes, (1., .5)):
        for mode in MODES:
            ax.plot(range(51), [100*x for x in series[E, mode]], label=labels[mode], color=colors[mode], linestyle=styles[mode], linewidth=2)
        ax.set(title=f'Environmental compatibility E = {E:g}', xlabel='Damage–healing cycle', xlim=(0,50), ylim=(0,105))
        ax.grid(alpha=.2)
    axes[0].set_ylabel('Strength retained (% of initial reference)')
    axes[1].legend(loc='upper right', fontsize=9)
    fig.suptitle('Illustrative model: repeated damage and partial recovery')
    fig.savefig(OUT/'strength_trajectories.png', dpi=300)
    fig.savefig(OUT/'strength_trajectories.svg')
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(11, 7), layout='constrained')
    names = {'d':'Damage fraction d', 'r':'Repairable fraction r', 'p':'Initial penalty p', 'h0':'Baseline recovery h₀', 'E':'Environmental factor E', 'q':'Availability retention q'}
    for ax, parameter in zip(axes.flat, ranges):
        for mode in MODES:
            rows = [row for row in sensitivity if row['parameter']==parameter and row['case']==mode]
            ax.plot([row['value'] for row in rows], [100*row['P50'] for row in rows], color=colors[mode], linestyle=styles[mode], label=labels[mode])
        ax.axvline(BASE[parameter], color='#999999', linewidth=.8, alpha=.6)
        ax.set(xlabel=names[parameter], ylabel='Strength after 50 cycles (%)', ylim=(0,100))
        ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('One-at-a-time sensitivity: assumed ranges, other inputs fixed')
    fig.savefig(OUT/'sensitivity.png', dpi=300)
    fig.savefig(OUT/'sensitivity.svg')
    plt.close(fig)
    print('All checks passed. Completed 6 baseline cases and 1,818 sensitivity runs.')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
