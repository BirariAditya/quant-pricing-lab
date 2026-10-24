# Contributing

Use Python 3.10+ and a virtual environment. Install development and reference dependencies:

```bash
python -m pip install -e ".[validation,dev]"
```

Before opening a pull request:

```bash
ruff check .
python -m unittest discover -s tests -v
python scripts/validate_quantlib.py
python -m build
```

For a numerical change, explain the model assumptions, units, failure case, and reference
calculation. Add a regression case that fails before the fix. For stochastic work, report seeds,
sampling units, preparation costs, and the comparison budget; one favorable run is not evidence
of a general improvement. Avoid tests requiring every nominal 95% interval to contain the reference.

Keep generated results reproducible using the scripts in `scripts/`. Numerical outputs can vary
slightly across dependency versions and platforms; elapsed-time results are machine-specific.
Do not include credentials, private datasets, or proprietary code.
