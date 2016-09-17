#!/usr/bin/env python3
# Install dependencies from a "[metadata] setup-requires = ..." section in
# setup.cfg, then run real-setup.py (or inline setup.py)
# From https://bitbucket.org/dholth/setup-requires

import os
import configparser
import pkg_resources
import sys
import subprocess
import versioneer
from setuptools import setup, find_packages


DESCRIPTION = "Rootspace Game, Yay!"
LONG_DESCRIPTION = ""
DIST_NAME = "rootspace"
LICENSE = "MIT"
AUTHOR = "Eleanore C. Young"
EMAIL = ""
URL = ""
DOWNLOAD_URL = ""
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: End Users",
    "Topic :: Games :: Casual",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3"
]
KEYWORDS = "game, casual, point-and-click, hacking"


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


if __name__ == "__main__":
    sys.path[0:0] = ["setup-requires"]
    pkg_resources.working_set.add_entry("setup-requires")

    try:
        to_install = list(get_requirements())
        if to_install:
            subprocess.call([sys.executable, "-m", "pip", "install", "-t", "setup-requires"] + to_install)

    except (configparser.NoSectionError, configparser.NoOptionError):
        pass

    setup(
        name=DIST_NAME,
        author=AUTHOR,
        author_email=EMAIL,
        description=DESCRIPTION,
        license=LICENSE,
        url=URL,
        download_url=DOWNLOAD_URL,
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS,
        long_description=LONG_DESCRIPTION,
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        platforms="any",
        install_requires=[
            "click",
            "attrs",
            "numpy",
            "pysdl2"
        ],
        test_requires=[
            "pytest"
        ],
        entry_points={
            "console_scripts": [
                "rootspace = rootspace.main:main"
            ]
        },
        packages=find_packages(where="src", exclude=("historical", "tests", "specs")),
        package_dir={"": "src"},
        package_data={
            "rootspace": ["config.ini", "keymap.ini"]
        }
    )
