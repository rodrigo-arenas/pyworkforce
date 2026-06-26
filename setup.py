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
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    project_urls={
        "Documentation": "https://rodrigo-arenas.github.io/pyworkforce/",
        "Source Code": "https://github.com/rodrigo-arenas/pyworkforce",
        "Bug Tracker": "https://github.com/rodrigo-arenas/pyworkforce/issues",
    },
    packages=find_packages(include=['pyworkforce', 'pyworkforce.*']),
    install_requires=[
        'numpy>=1.26.0',
        'ortools>=9.12.4544',
        'pandas>=2.2.0',
        'joblib>=1.4.0'
    ],
    python_requires=">=3.12,<3.15",
    include_package_data=True,
)
