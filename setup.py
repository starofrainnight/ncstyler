#!/usr/bin/env python

from pydgutils_bootstrap import use_pydgutils
use_pydgutils()

import os
import os.path
import sys
import pydgutils
from setuptools import setup, find_packages
from pip.req import parse_requirements

package_name = 'ncstyler'

# Convert source to v2.x if we are using python 2.x.
source_dir = pydgutils.process()

# Exclude the original source package, only accept the preprocessed package!
our_packages = find_packages(where=source_dir)

# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = parse_requirements("./requirements.txt", session=False)
requirements = [str(ir.req) for ir in requirements]

long_description=(
     open("README.rst", "r").read()
     + "\n" +
     open("CHANGES.rst", "r").read()
     )

setup(
    name=package_name,
    version="0.1.5",
    author="Hong-She Liang",
    author_email="starofrainnight@gmail.com",
    url="https://github.com/starofrainnight/%s" % package_name,
    description="Name Conventions Styler, a styler just target to naming conventions of source codes",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
    ],
    install_requires=requirements,
    package_dir = {"": source_dir},
    packages=our_packages,
    entry_points = {
        'console_scripts': ['ncstyler=ncstyler.console:main'],
    },
    zip_safe=False, # Unpack the egg downloaded_file during installation.
    )
