# Release Notes

## 0.53.0 (development)

### New features

- **`pyworkforce.queuing.ErlangA`** — a new M/M/c+M queue model with customer
  **abandonment** (patience). Exposes `waiting_probability`,
  `abandonment_probability`, `achieved_occupancy`, `average_speed_of_answer`,
  `average_queue_length`, an exact `service_level`, and `required_positions`
  with service-level, occupancy and abandonment targets. All metrics are
  computed exactly from the birth-death stationary distribution and verified
  against a Monte Carlo simulation and the Erlang C patient limit.
- **`pyworkforce.queuing.MultiErlangA`** — the abandonment-aware counterpart of
  `MultiErlangC`: evaluates `ErlangA` over a parameter grid in parallel.
- **`pyworkforce.shifts`** — builders to create `shifts_coverage` definitions
  without hand-writing 0/1 arrays: `shift_coverage_from_hours`,
  `shift_coverage_from_spans`, `shift_coverage_from_periods`, plus
  `validate_shift_coverage` and `coverage_to_dataframe`.
- **`pyworkforce.utils.results_to_dataframe`** — turn `Multi*` results (and the
  parameters that produced them) into a tidy `pandas.DataFrame`.
- All estimators now provide `get_params()` and a readable `repr()`
  (`BaseWorkforce` mixin), and store their last result as `solution_`.

### Bug fixes

- **`MultiErlangC`** now correctly populates `achieved_occupancy_params` and
  `required_positions_params` (previously always `None`).
- Validation helpers no longer reject integers where a float is expected (for
  example `max_search_time=240`) and now reject booleans, `NaN` and infinities.
- `MinHoursRoster` rejects duplicate resource names, which previously caused
  silent index-lookup errors for banned shifts and preferences.

### API quality

- Schedulers and `MinHoursRoster` validate their inputs and shapes up front
  with clear, consistent `ValueError` / `KeyError` messages.
- Greatly expanded test suite (35 → 120+ tests) and higher coverage.

### Packaging & tooling

- Migrated packaging from `setup.py` to a PEP 621 **`pyproject.toml`**.
- Upgraded dependency floors (`numpy>=2.0`, `pandas>=2.2`, `ortools>=9.14`,
  `joblib>=1.4.2`); development extras are now installed with
  `pip install -e ".[dev]"`.
- Added [ruff](https://docs.astral.sh/ruff/) linting, enforced in CI.
- CI now runs a lint gate, cancels superseded runs, and tests against the
  latest dependencies. Added a Dependabot config and a PyPI
  trusted-publishing release workflow.

### API

- Estimator constructors no longer silently accept unknown keyword arguments,
  so typos in parameter names now raise a clear `TypeError`.

### Documentation

- Documentation moved from Read the Docs / Sphinx to a
  [VitePress](https://vitepress.dev/) site published on **GitHub Pages**.
- Added self-contained, notebook-style tutorials with real outputs: an
  end-to-end queue → schedule → roster walkthrough and a scenario-comparison
  guide using the grid estimators and `results_to_dataframe`.

## 0.5.2

- Latest Python support (3.12–3.14) and CI / packaging updates.

For older releases, see the
[GitHub releases page](https://github.com/rodrigo-arenas/pyworkforce/releases).
