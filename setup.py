import os
import pathlib
from setuptools import setup, find_packages

# python setup.py sdist bdist_wheel
# twine upload --skip-existing dist/*

# get __version__ from _version.py
ver_file = os.path.join("pyworkforce", "_version.py")
with open(ver_file) as f:
    exec(f.read())

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="pyworkforce",
    version=__version__,
    description="Common tools for workforce management, schedule and optimization problems",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/rodrigo-arenas/pyworkforce",
    author="Rodrigo Arenas",
    author_email="rodrigo.arenas456@gmail.com",
    license="MIT",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    project_urls={
        "Documentation": "https://pyworkforce.readthedocs.io/en/stable/",
        "Source Code": "https://github.com/rodrigo-arenas/pyworkforce",
        "Bug Tracker": "https://github.com/rodrigo-arenas/pyworkforce/issues",
    },
    packages=find_packages(include=['pyworkforce', 'pyworkforce.*']),
    install_requires=[
        'numpy>=1.23.0',
        'ortools>=9.2.9972',
        'pandas>=1.3.5',
        'joblib>0.17'
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
