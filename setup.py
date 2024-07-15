#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing qpc."""

import sys
from pathlib import Path

from setuptools import find_packages, setup

from qpc.release import (
    ENTRYPOINT,
    URL,
    VERSION,
)

BASE_QPC_DIR = Path(__file__).absolute().parent
sys.path.insert(0, BASE_QPC_DIR / "qpc")

setup(
    name="qpc",
    version=VERSION,
    include_package_data=True,
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
