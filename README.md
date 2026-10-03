# Self-healing simulation

Python code and generated results accompanying *Self-Healing Composite Materials for Aerospace Structures: Mechanisms, Space-Environment Constraints, and a Computational Assessment of Damage Recovery*.

This exploratory model implements manuscript Sections 5.2–5.9. All numerical inputs are assumed rather than experimentally measured. Environmental factors E = 1 and E = 0.5 are illustrative settings, not aircraft or spacecraft calibrations. All strengths are normalized by the initial strength of the non-healing reference.

## Installation and running

Python 3 and Matplotlib 3.11.2 are required. From the repository folder, run:

```bash
python -m pip install matplotlib==3.11.2
python run_all.py
```

On Windows, use `py` instead of `python` if required by your installation.

To run the scripts separately:

```bash
python simulation.py
python robustness.py
python horizon_analysis.py
```

The scripts regenerate data and figures in `results/`, overwriting existing generated files. Calculations use the Python standard library; Matplotlib generates the figures. MATLAB is not required.

Generated results are included for inspection without running the code.

## Model and baseline settings

The model applies fractional damage followed by partial recovery during each cycle. Healing can restore only the current cycle’s loss; previously unrecovered damage remains.

Baseline inputs:

- Number of cycles: 50
- Damage fraction: d = 0.03
- Repairable fraction: r = 0.75
- Initial strength penalty for healing cases: p = 0.05
- Baseline healing capability: h₀ = 0.80
- Availability retention: q = 0.95

The reference has zero initial penalty and no healing. Sustained healing uses availability Aₙ = 1. Declining healing uses Aₙ = qⁿ⁻¹.

Baseline simulations examine E = 1 and E = 0.5. Trajectories include cycle zero. Strengths in CSV files are fractions; graphs show percentages.

## Sensitivity and break-even analyses

The one-at-a-time analysis uses 101 equally spaced values for each parameter:

| Parameter | Range |
|---|---|
| Damage fraction, d | 0.01–0.05 |
| Repairable fraction, r | 0–1 |
| Initial penalty, p | 0–0.15 |
| Baseline healing capability, h₀ | 0–1 |
| Environmental factor, E | 0–1 |
| Availability retention, q | 0.90–1.00 |

Other inputs remain at baseline, with E = 1 except during its own sweep. All three cases are evaluated, producing 1,818 runs. The reference retains zero penalty and zero healing; q affects only declining healing.

The joint analysis evaluates 101 values of E from 0 to 1 and 101 values of q from 0.90 to 1.00 for both healing cases, producing 20,402 cases. Sustained-healing results repeat across q because that parameter does not affect sustained availability.

Break-even calculations determine:

- The environmental factor at which each healing case equals the reference at cycle 50, with p = 0.05.
- The initial penalty that gives equality with the reference at cycle 50 for E = 1 and E = 0.5.

Environmental thresholds use 60 bisection iterations. All other inputs remain at baseline. These thresholds are model comparisons, not acceptable design penalties or aerospace qualification criteria.

The horizon analysis compares break-even initial penalties at 10, 50 and 100 cycles for E = 1, holding the remaining damage and healing inputs at baseline. It also evaluates the finite long-term penalty limit for declining availability. Results and settings are saved in horizon_summary.csv and horizon_settings.json. These thresholds describe equality with the damaged reference, not acceptable design penalties.

The selected ranges are exploratory. These analyses do not establish statistical uncertainty or a universal ranking of parameter importance.

## Generated files

All outputs are stored in `results/`.

| File | Contents |
|---|---|
| `summary.csv` | Baseline final strengths and crossover cycles |
| `trajectories.csv` | Baseline strength trajectories |
| `sensitivity.csv` | One-at-a-time sensitivity results |
| `settings.json` | Baseline and sensitivity settings |
| `joint_sensitivity.csv` | Joint E/q results |
| `break_even.json` | Break-even thresholds |
| `horizon_summary.csv` | Equality penalties at 10, 50 and 100 cycles |
| `horizon_settings.json` | Horizon-analysis settings and declining-availability limit |
| `strength_trajectories.png` / `.svg` | Baseline trajectory figure |
| `sensitivity.png` / `.svg` | One-at-a-time sensitivity figure |

PNG figures can be inserted into documents; SVG figures provide scalable graphics. Displayed values are rounded, while CSV and JSON files retain calculation precision.

## Verification and limitations

Implementation checks cover a closed-form constant-parameter solution, performance bounds, zero damage, zero healing, complete recovery, availability endpoints, and analytical break-even relationships.

These checks verify mathematical implementation, not agreement with experimental behaviour. The model has not been calibrated or independently validated against material-test data. Consequently, no physical prediction-error bound or statistical confidence interval is established.

Recovery factors cannot be identified separately from a strength trajectory without additional observations or constraints. Cycles represent abstract damage–healing events, not flights, impacts of specified energy, or orbital periods.

No random sampling is used. Identical inputs reproduce the numerical results within floating-point precision; figure rendering may vary with software versions.

The outputs must not be presented as experimental measurements, service-life predictions, or evidence of aerospace qualification.
