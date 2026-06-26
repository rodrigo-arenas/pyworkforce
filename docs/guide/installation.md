# Installation

pyworkforce supports **Python 3.12, 3.13 and 3.14**.

## pip

```bash
pip install pyworkforce
```

This works on Linux, macOS, and Windows.

## conda

conda-forge support is **not yet available**. The `ortools-python` feedstock on
conda-forge does not yet ship Python 3.12 builds, which is required by pyworkforce.
Use pip in the meantime.

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
