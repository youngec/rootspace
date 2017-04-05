#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Install dependencies from a "[metadata] setup-requires = ..." section in
# setup.cfg, then run real-setup.py (or inline setup.py)
# From https://bitbucket.org/dholth/setup-requires

import configparser
import os
import subprocess
import sys

import pkg_resources
from setuptools import setup, find_packages, Extension

import versioneer


def get_requirements():
    """
    Get the project's setup-requires requirements from setup.cfg.

    :return:
    """
    if not os.path.exists("setup.cfg"):
        return

    config = configparser.ConfigParser()
    config.read("setup.cfg", encoding="utf-8")
    setup_requires = config.get("metadata", "setup-requires")
    specifiers = [line.strip() for line in setup_requires.splitlines()]
    for specifier in specifiers:
        try:
            pkg_resources.require(specifier)
        except pkg_resources.DistributionNotFound:
            yield specifier


def read(path):
    """
    Read a file at the specified path and return its contents.

    :param path:
    :return:
    """
    full_path = os.path.realpath(path)
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    sys.path[0:0] = ["setup-requires"]
    pkg_resources.working_set.add_entry("setup-requires")

    try:
        pip_call = [
            sys.executable, "-m", "pip", "install", "-t", "setup-requires"
        ]
        to_install = list(get_requirements())
        if to_install:
            subprocess.call(pip_call + to_install)

    except (configparser.NoSectionError, configparser.NoOptionError):
        pass

    math_opt = Extension("rootspace._math", [
        "src/rootspace/_math.c",
        "src/rootspace/_matrix.c",
        "src/rootspace/_matrix_container.c",
        "src/rootspace/_index_handling.c",
        "src/rootspace/_matrix_iterator.c"
    ])

    setup(
        name="rootspace",
        author="Eleanore C. Young",
        author_email="",
        description="A hackneyed attempt at a Python-based game.",
        long_description=read("README.rst"),
        keywords="game, casual, point-and-click, hacking",
        license="MIT",
        url="https://github.com/youngec/rootspace.git",
        download_url="https://github.com/youngec/rootspace.git",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: End Users",
            "Topic :: Games :: Casual",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3"
        ],
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        platforms="any",
        ext_modules=[math_opt],
        install_requires=[
            "attrs == 16.3.0",
            "glfw == 1.4.0",
            "pyopengl == 3.1.0",
            "xxhash == 1.0.1",
            "pillow == 4.1.0",
            "pyparsing == 2.2.0",
            "regex == 2017.2.8"
        ],
        tests_require=[
            "pytest == 3.0.7",
            "pytest-pep8 == 1.0.6",
            "pytest-mock == 1.6.0",
            "pytest-benchmark == 3.0.0"
        ],
        entry_points={
            "console_scripts": [
                "rootspace = rootspace.main:main"
            ]
        },
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        package_data={}
    )
