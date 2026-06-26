# Release Notes

## 0.5.4

### New features

- **`pyworkforce.staffing.MultiSkillStaffing`** — minimum-cost agent-mix
  optimiser for multi-skill contact-centre staffing. Given per-skill requirements
  (from `ErlangC` / `ErlangA`) and a catalogue of agent skill profiles, solves
  the integer programme that minimises total weighted headcount. Flexible
  (multi-skilled) agents count towards every skill they hold, so the solver
  automatically balances dedicated vs. flexible hiring. Supports an optional
  `max_agents` budget cap and is now exported from the `pyworkforce` root namespace.

## 0.5.3

### New features

- **`pyworkforce.queuing.ErlangB`** / **`MultiErlangB`** — Erlang B (M/M/c/c)
  pure-loss queue for trunk and channel sizing. Models systems with no waiting
  room where blocked calls are shed. Provides `blocking_probability`,
  `achieved_occupancy` and `required_positions` (with `max_blocking` and
  `max_occupancy` targets). `MultiErlangB` sweeps a parameter grid in parallel,
  mirroring `MultiErlangC`.
- **`pyworkforce.breaks.BreakScheduler`** — CP-SAT solver that assigns break
  start times to agent slots within each shift while enforcing break windows
  (earliest start, latest end), preventing overlapping breaks on the same slot,
  and guaranteeing that simultaneous breaks never exceed the coverage slack.
  Accepts multiple break types per shift.
- Both are now exported from the `pyworkforce` root namespace.

### Dependency changes

- Lowered `numpy` floor to `>=1.23` (code uses only stable basic operations;
  aligns with the `pandas>=2.2` minimum and unblocks the conda-forge package).
- Lowered `ortools` floor to `>=9.6` (all CP-SAT APIs in use are stable at
  this version; matches the conda-forge `ortools-python` feedstock).

## 0.5.2 — *previous release*

### New features

- **`pyworkforce.queuing.ErlangA`** — M/M/c+M queue with customer abandonment.
  All metrics computed exactly from the birth-death stationary distribution.
- **`pyworkforce.queuing.MultiErlangA`** — parameter-grid variant of `ErlangA`.
- **`pyworkforce.shifts`** — shift coverage builders (`shift_coverage_from_hours`,
  `shift_coverage_from_spans`, `shift_coverage_from_periods`,
  `validate_shift_coverage`, `coverage_to_dataframe`).
- **`pyworkforce.utils.results_to_dataframe`** — tidy DataFrames from `Multi*`
  results.
- All estimators expose `get_params()`, a readable `repr()` and store their
  last result as `solution_`.

### Bug fixes

- `MultiErlangC` now correctly populates `achieved_occupancy_params` and
  `required_positions_params`.
- Validation helpers accept integers where floats are expected and reject
  booleans, `NaN` and infinities.
- `MinHoursRoster` rejects duplicate resource names.

### Packaging & tooling

- Migrated to PEP 621 `pyproject.toml`; upgraded dependency floors.
- Added ruff linting, Dependabot config, and a PyPI trusted-publishing workflow.
- Documentation moved to VitePress on GitHub Pages.

## 0.5.2

- Latest Python support (3.12–3.14) and CI / packaging updates.

For older releases, see the
[GitHub releases page](https://github.com/rodrigo-arenas/pyworkforce/releases).
