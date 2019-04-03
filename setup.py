#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing qpc."""
import os
import sys
import json

from setuptools import find_packages, setup

with open('qpc/settings.json') as json_file:
    settings = json.load(json_file)

BASE_QPC_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]), '.')))
sys.path.insert(0, os.path.join(BASE_QPC_DIR, 'qpc'))
# pylint: disable=wrong-import-position
from qpc import __version__  # noqa: E402, I100

setup(
    name=settings['package_name'],
    version=__version__,
    author=settings['author'],
    author_email=settings['author_email'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    include_package_data=True,
    license='GPLv3',
    packages=find_packages(exclude=['test*.py']),
    package_data={'': ['LICENSE', 'settings.json']},
    url='https://github.com/quipucords/qpc',
    scripts=[
        settings['bin_script'],
    ],
    zip_safe=False
)
