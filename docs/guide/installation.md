# Installation

pyworkforce supports **Python 3.12, 3.13 and 3.14**.

## pip

Available on all platforms (Linux, macOS, Windows):

```bash
pip install pyworkforce
```

## conda

```bash
conda install -c conda-forge pyworkforce
```

> **Platform limitation:** the conda-forge package is currently **Linux (x86-64) only**.
> This is because `ortools-python` — pyworkforce's constraint-solver dependency — is
> not yet available in the conda-forge channel for macOS or Windows.
> macOS and Windows users should install via pip instead.
>
> **numpy version:** conda-forge's `ortools-python 9.6` pins `numpy <2.0`, so the
> conda package resolves with numpy 1.x. If you need numpy 2.x, install via pip.
>
> Both limitations will be lifted automatically once the
> [ortools-python feedstock](https://github.com/conda-forge/ortools-python-feedstock)
> is updated to a version that supports all platforms and numpy 2.x.

## Requirements

pyworkforce depends on:

- [numpy](https://numpy.org/)
- [pandas](https://pandas.pydata.org/)
- [ortools](https://developers.google.com/optimization) (constraint solver)
- [joblib](https://joblib.readthedocs.io/) (parallel scenario evaluation)

These are installed automatically with either command above.

## Verify the installation

```python
import pyworkforce
print(pyworkforce.__version__)
```

## Development install

To work on pyworkforce itself, clone the repository and install it in editable
mode with the development requirements:

```bash
git clone https://github.com/rodrigo-arenas/pyworkforce.git
cd pyworkforce
pip install -e ".[dev]"
pytest pyworkforce/
ruff check pyworkforce/
```
