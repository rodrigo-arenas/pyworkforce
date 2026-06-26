# Installation

pyworkforce is published on [PyPI](https://pypi.org/project/pyworkforce/). We
recommend installing it inside a virtual environment.

```bash
pip install pyworkforce
```

## Requirements

pyworkforce supports **Python 3.12, 3.13 and 3.14** and depends on:

- [numpy](https://numpy.org/)
- [pandas](https://pandas.pydata.org/)
- [ortools](https://developers.google.com/optimization) (constraint solver)
- [joblib](https://joblib.readthedocs.io/) (parallel scenario evaluation)

These are installed automatically with the command above.

## Anaconda

If you are using Anaconda and run into installation issues, update the
environment first:

```bash
conda update --all
```

If the problem is related to OR-Tools, see the
[OR-Tools installation guide](https://github.com/google/or-tools#installation).

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
pip install -e . -r dev-requirements.txt
pytest pyworkforce/
```
