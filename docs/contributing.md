# Contributing

Contributions are welcome across code, examples, documentation, tests, and
planning scenarios. This page is the short docs-site version; the full workflow
lives in [CONTRIBUTING.md](https://github.com/rodrigo-arenas/pyworkforce/blob/main/CONTRIBUTING.md).

## Local setup

```bash
git clone https://github.com/<your-username>/pyworkforce.git
cd pyworkforce
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

pyworkforce targets Python 3.12, 3.13, and 3.14.

## Checks

```bash
ruff check pyworkforce/
pytest pyworkforce/ --cov=pyworkforce --cov-fail-under=95
```

Documentation uses VitePress:

```bash
cd docs
npm install
npm run docs:dev
npm run docs:build
```

## Good first contributions

- Add runnable examples for healthcare, retail, logistics, service desks, or
  field operations.
- Improve validation messages and edge-case tests.
- Add benchmark scenarios for larger scheduling and rostering cases.
- Build small visualization helpers for coverage and schedules.
- Document additional workforce constraints and how to model them.
- Translate or localize selected docs pages.
- Add comparison notebooks against spreadsheet-style calculations.

## Documentation guidelines

For each major module, aim to include:

- the business problem being solved;
- when to use the model and when not to use it;
- input format and units;
- a copy-paste runnable example;
- expected output and how to interpret it;
- common pitfalls.

Keep examples small enough to read, but realistic enough that a workforce
analyst can recognize the use case.
