#!/usr/bin/env python

from rabird_bootstrap import use_rabird
use_rabird()
    
import os
import os.path
import sys
import shutil
import logging
import fnmatch
import glob
import zipfile
import shutil
from six.moves import urllib
import math
import rabird.core.distutils
import rabird.core.logging
from setuptools import setup, find_packages

package_name = 'ncstyler'

# Convert source to v2.x if we are using python 2.x.
source_dir = rabird.core.distutils.preprocess_source()

# Exclude the original source package, only accept the preprocessed package!
our_packages = find_packages(where=source_dir)

our_requires = []

long_description=(
     open("README.rst", "r").read()
     + "\n" +
     open("CHANGES.rst", "r").read()
     )

setup(
    name=package_name,
    version="0.0.1",
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
    install_requires=our_requires,
    package_dir = {"": source_dir},
    packages=our_packages,
    entry_points = {
        'console_scripts': ['ncstyler=ncstyler.console:main'],
    },
    zip_safe=False, # Unpack the egg downloaded_file during installation.
    )
