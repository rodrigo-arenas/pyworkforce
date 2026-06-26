# Installation

pyworkforce supports **Python 3.12, 3.13 and 3.14** and is available on both
PyPI and conda-forge.

## pip

```bash
pip install pyworkforce
```

## conda

```bash
conda install -c conda-forge pyworkforce
```

> **Note:** the `ortools-python` package on conda-forge may lag behind the
> PyPI release of OR-Tools. If you need the latest OR-Tools version or
> encounter solver issues, install via pip instead, or see the
> [OR-Tools installation guide](https://github.com/google/or-tools#installation).

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
