#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
setup.py was assembled with help from https://packaging.python.org/en/latest/
"""

import sys
from os import path
from codecs import open  # To use a consistent encodingA

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from setuptools.command.test import test as TestCommand

from rootspace.version import VERSION


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


# Get the long description from the relevant file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, "DESCRIPTION.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rootspace",
    version=VERSION,
    url="",
    license="MIT",
    author="Eleanore Young",
    author_email="",
    description="Rootspace",
    long_description=long_description,
    keywords="game, casual, point-and-click, hacking",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users",
        "Topic :: Games :: Casual",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(exclude=["contrib", "docs", "tests", "puppet", "log"]),
    package_data={
        "rootspace": ["config.ini", "keymap.ini"]
    },
    install_requires=["click", "characteristic", "pillow", "numpy", "pysdl2"],
    tests_require=["pytest"],
    cmdclass={"test": PyTest},
    entry_points={
        "console_scripts": [
            "rootspace=rootspace.loader:main"
        ],
    },
)
