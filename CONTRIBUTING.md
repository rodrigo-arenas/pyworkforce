# Contributing to pyworkforce

Thanks for your interest in improving pyworkforce! Contributions of all kinds
are welcome — bug reports, feature requests, documentation and code. This guide
walks through setting up a local environment and the checks we run.

## Table of contents

- [Reporting issues](#reporting-issues)
- [Local development setup](#local-development-setup)
- [Project layout](#project-layout)
- [Running the tests](#running-the-tests)
- [Linting and formatting](#linting-and-formatting)
- [Working on the documentation](#working-on-the-documentation)
- [Adding models, examples and docs](#adding-models-examples-and-docs)
- [Contributor roadmap](#contributor-roadmap)
- [Pull request workflow](#pull-request-workflow)

## Reporting issues

- **Bugs:** open an issue with a minimal, reproducible example, the full
  traceback, and your Python / pyworkforce versions.
- **Features:** describe the use case and, ideally, the API you'd like to see.

Use the issue templates under
[`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE) where they apply.

## Local development setup

pyworkforce targets **Python 3.12–3.14**. You only need Python and git for the
library; Node.js is needed only if you work on the docs.

1. Fork the repository on GitHub, then clone your fork:

   ```bash
   git clone https://github.com/<your-username>/pyworkforce.git
   cd pyworkforce
   ```

2. Create and activate a development environment.

   **Using venv:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -e ".[dev]"
   ```

   **Using conda / mamba:**

   ```bash
   conda create -n pyworkforce python=3.12
   conda activate pyworkforce
   pip install -e ".[dev]"
   ```

   Either way, the editable install pulls in the runtime deps plus `pytest`,
   `pytest-cov`, `ruff` and `twine`.

3. Check that everything imports and the suite is green:

   ```bash
   python -c "import pyworkforce; print(pyworkforce.__version__)"
   pytest pyworkforce/
   ```

> [!TIP]
> All configuration (build metadata, dependencies, `ruff`, `pytest` and coverage
> settings) lives in a single [`pyproject.toml`](pyproject.toml).

## Project layout

```
pyworkforce/
├── queuing/       # ErlangC, ErlangA, MultiErlangC, MultiErlangA
├── scheduling/    # MinAbsDifference, MinRequiredResources
├── rostering/     # MinHoursRoster
├── shifts/        # shift-coverage builders
├── utils/         # ParameterGrid, validation, results_to_dataframe
├── base.py        # BaseWorkforce mixin (get_params / repr)
└── */tests/       # tests live next to the code they cover
docs/              # VitePress documentation site
examples/          # runnable example scripts
```

## Running the tests

We use [pytest](https://docs.pytest.org/) and
[pytest-cov](https://pytest-cov.readthedocs.io/).

```bash
# Whole suite
pytest pyworkforce/

# A single module or test
pytest pyworkforce/queuing/tests/test_abandonment.py
pytest pyworkforce/queuing/tests/test_abandonment.py::test_erlanga_regression_metrics

# With coverage (CI requires the total to stay at or above 95%)
pytest pyworkforce/ --cov=pyworkforce --cov-report=term-missing --cov-fail-under=95

# Docstring examples
pytest --doctest-modules pyworkforce/
```

Guidelines:

- **New features and bug fixes should come with tests.** Add them next to the
  code, under the module's `tests/` folder.
- Keep coverage at or above **95%**. Mark genuinely unreachable defensive
  branches with `# pragma: no cover` rather than writing contrived tests.
- **Validate numerical methods against an independent reference** where
  practical. For example, `ErlangA` is checked against a Monte Carlo simulation
  and against the Erlang C limit (as patience → ∞).

## Linting and formatting

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting. The
CI **lint gate runs `ruff check`**, and the test matrix only runs after it
passes, so please run it locally first.

```bash
# Lint (this is what CI enforces)
ruff check pyworkforce/

# Auto-fix the issues ruff can fix safely (import order, f-strings, ...)
ruff check --fix pyworkforce/

# Format code you changed (ruff is also a formatter)
ruff format pyworkforce/
```

A few conventions worth knowing (all configured in `pyproject.toml`):

- Line length is 120.
- Tests may keep unused bindings (e.g. constructing inside `pytest.raises`).
- `pyworkforce/utils/grid.py` is vendored from scikit-learn and is intentionally
  left close to upstream.

## Working on the documentation

The docs are a [VitePress](https://vitepress.dev/) site under `docs/` and need
Node.js (18+):

```bash
cd docs
npm install
npm run docs:dev       # local dev server with hot reload
npm run docs:build     # build the static site
```

When you change documented behavior, please:

- update the relevant guide / API page under `docs/`;
- keep tutorial code blocks runnable and show **real** outputs (run the snippet
  and paste what it prints);
- add an entry to the release notes (`docs/release-notes.md`).

## Adding models, examples and docs

### Adding a new solver or model

New optimization models should fit the existing project style:

- Put the implementation in the closest domain package (`queuing`, `staffing`,
  `scheduling`, `rostering`, `breaks`, or a new package only when the domain is
  genuinely new).
- Keep the public API explicit: constructor arguments should be named, validated
  up front, and documented.
- Return a plain dictionary from `solve()` / sizing methods, and store the last
  result on `solution_` where that pattern applies.
- Prefer clear `ValueError` messages for invalid user input rather than letting
  OR-Tools, NumPy, or pandas fail later with low-level errors.
- Add focused tests next to the module under `*/tests/`. Include infeasible or
  invalid-input cases when they are part of the expected behavior.
- Document the business problem, assumptions, inputs, output interpretation, and
  common pitfalls before opening the PR.

For numerical queueing models, validate against an independent reference where
possible: published formulas, a small brute-force calculation, a simulation, or
known limiting behavior.

### Adding examples

Examples under `examples/` should be runnable with:

```bash
python examples/path/to/example.py
```

Keep datasets small and inline unless the point of the example is file I/O.
Use business-friendly names (`Billing`, `Technical`, `Morning`, `Night`) and
print the key output a user should inspect. If an example needs a larger data
file, include a short note explaining how to scale the pattern to real data.

Good example themes:

- contact center staffing with Erlang C, Erlang A, and Erlang B;
- multi-skill staffing for language or support queues;
- shift coverage from hourly demand;
- named roster generation with banned shifts and preferences;
- break scheduling while preserving minimum coverage;
- end-to-end planning pipelines that join several modules.

### Documentation guidelines

Every major guide should answer the same practical questions:

- **Problem statement:** what business decision does this model support?
- **When to use it:** what assumptions make it appropriate?
- **Input format:** shape, units, and key constraints.
- **Code example:** copy-paste runnable and small enough to understand.
- **Output explanation:** what each important field means.
- **Common pitfalls:** units, infeasibility, assumptions, or modeling traps.

Do not over-market. Make pyworkforce attractive by showing credible workflows,
realistic inputs, and clear outputs.

## Contributor roadmap

These are useful issue ideas for new and experienced contributors:

- More domain examples for healthcare staffing, retail operations, logistics,
  support teams, service desks, and field operations.
- Additional validation improvements for edge cases and clearer error messages.
- Benchmark scenarios for larger scheduling, rostering, and break-scheduling
  problems.
- Visualization helpers for demand curves, scheduled coverage, roster matrices,
  and break placement.
- Additional workforce constraints such as weekly hour caps, skill-specific
  rest rules, unavailable windows, fairness objectives, and weekend balancing.
- Documentation translations and glossary improvements for workforce planning
  terms.
- Comparison notebooks that show how pyworkforce results relate to common
  spreadsheet calculators and manual planning workflows.
- More examples that export results to pandas DataFrames or downstream BI tools.

## Pull request workflow

1. Create a feature branch off `main` and keep the PR focused on one change.
2. Make sure the checks pass locally:

   ```bash
   ruff check pyworkforce/
   pytest pyworkforce/ --cov=pyworkforce --cov-fail-under=95
   ```

3. Write a clear PR description: the motivation, a summary of the change, and any
   trade-offs. Reference related issues.
4. Update `docs/release-notes.md` for user-facing changes.
5. CI (lint + the test matrix across Python 3.12–3.14 on Linux, macOS and
   Windows) must be green before a PR is merged.

## Code of conduct

Be respectful and constructive. We want pyworkforce to be a welcoming project
for the community.
