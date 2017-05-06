#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provide a setuptools-based setup function. The get_setup_dependencies and
install_dependencies functions allow the project to install setup-time
dependencies. The idea is from https://bitbucket.org/dholth/setup-requires.
"""

import configparser
import os
import subprocess
import sys
import pathlib

import pkg_resources
from setuptools import setup, find_packages, Extension

import versioneer


def get_setup_dependencies():
    """
    Get the project's setup-requires requirements from setup.cfg.
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


def install_dependencies(dependencies):
    """
    Install the specified dependencies via PIP. Designed to be used
    before the actual call to setuptools.setup().
    """
    sys.path[0:0] = ["setup-requires"]
    pkg_resources.working_set.add_entry("setup-requires")
    pip_call = [
        sys.executable, "-m", "pip", "install", "-t", "setup-requires"
    ]
    if len(dependencies) > 0:
        subprocess.call(pip_call + dependencies)


if __name__ == "__main__":
    # Install the setup-time dependencies
    try:
        deps = list(get_setup_dependencies())
        install_dependencies(deps)
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass

    # Define the C-extension modules
    math_opt = Extension("rootspace._math", [
        "src/rootspace/_math.c",
        "src/rootspace/_matrix.c",
        "src/rootspace/_matrix_container.c",
        "src/rootspace/_index_handling.c",
        "src/rootspace/_matrix_iterator.c",
        "src/rootspace/_quaternion.c"
    ])

    long_description = pathlib.Path("README.md")

    setup(
        name="rootspace",
        author="Eleanore C. Young",
        author_email="",
        description="A hackneyed attempt at a Python-based game.",
        long_description=long_description.read_text(),
        keywords="game, casual, point-and-click, hacking",
        license="MIT",
        url="https://github.com/youngec/rootspace.git",
        download_url="https://github.com/youngec/rootspace.git",
        classifiers=(
            "Development Status :: 3 - Alpha",
            "Intended Audience :: End Users",
            "Topic :: Games :: Casual",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6"
        ),
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        platforms="any",
        ext_modules=[math_opt],
        install_requires=(
            "attrs == 16.3.0",
            "glfw == 1.4.0",
            "pyopengl == 3.1.0",
            "xxhash == 1.0.1",
            "pillow == 4.1.1",
            "pyparsing == 2.2.0",
            "regex == 2017.4.29"
        ),
        tests_require=(
            "pytest == 3.0.7",
            "pytest-pep8 == 1.0.6",
            "pytest-mock == 1.6.0",
            "pytest-benchmark == 3.0.0"
        ),
        entry_points={
            "console_scripts": (
                "rootspace = rootspace.main:main",
            )
        },
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        include_package_data=True,
    )
