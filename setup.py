#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing qpc."""
import sys
from pathlib import Path

from setuptools import find_packages, setup

from qpc.release import (
    AUTHOR,
    AUTHOR_EMAIL,
    ENTRYPOINT,
    QPC_VAR_PROGRAM_NAME,
    URL,
    VERSION,
)

BASE_QPC_DIR = Path(__file__).absolute().parent
sys.path.insert(0, BASE_QPC_DIR / "qpc")

setup(
    name=QPC_VAR_PROGRAM_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    include_package_data=True,
    license="GPLv3",
    packages=find_packages(
        exclude=[
            "**/test_*.py",
            "**/*_tests.py",
            "**/tests_*.py",
        ]
    ),
    package_data={"": ["LICENSE"]},
    url=URL,
    entry_points={"console_scripts": [ENTRYPOINT]},
    zip_safe=False,
)
