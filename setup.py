import pathlib
from setuptools import setup, find_packages

# twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="pyworkforce",
    version="0.3.0",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(include=['pyworkforce', 'pyworkforce.*']),
    install_requires=[
        'numpy>=1.18.1',
        'ortools>=7.8.7959',
        'pandas>=1.0.0'
    ],
    python_requires=">=3.6",
    include_package_data=True,
)
