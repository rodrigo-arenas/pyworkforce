# Contributing to pyworkforce

Thanks for your interest in improving pyworkforce! Contributions of all kinds
are welcome — bug reports, feature requests, documentation and code.

## Development setup

pyworkforce targets Python 3.12–3.14.

```bash
git clone https://github.com/rodrigo-arenas/pyworkforce.git
cd pyworkforce
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the checks

Please make sure the following pass before opening a pull request:

```bash
# Tests + coverage (the CI gate requires >= 95%)
pytest pyworkforce/ --cov=pyworkforce

# Linting
ruff check pyworkforce/
```

New features and bug fixes should come with tests. Numerical methods should be
validated against an independent reference where practical (for example, the
Erlang A model is checked against a Monte Carlo simulation and the Erlang C
limit).

## Documentation

The docs are a [VitePress](https://vitepress.dev/) site under `docs/`:

```bash
cd docs
npm install
npm run docs:dev
```

## Pull requests

- Branch off `main` and keep pull requests focused.
- Describe the motivation and summarize the change.
- Update the release notes (`docs/release-notes.md`) for user-facing changes.

## Code of conduct

Be respectful and constructive. We want pyworkforce to be a welcoming project
for the community.
