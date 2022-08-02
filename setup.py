#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing qpc."""
import os
import sys

from setuptools import find_packages, setup

from qpc.release import AUTHOR, AUTHOR_EMAIL, BIN_SCRIPT, PKG_NAME, URL, VERSION

BASE_QPC_DIR = os.path.abspath(
    os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), "."))
)
sys.path.insert(0, os.path.join(BASE_QPC_DIR, "qpc"))

setup(
    name=PKG_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    include_package_data=True,
    license="GPLv3",
    packages=find_packages(exclude=["test*.py"]),
    package_data={"": ["LICENSE"]},
    url=URL,
    scripts=[
        BIN_SCRIPT,
    ],
    zip_safe=False,
)
