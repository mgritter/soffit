"""A setuptools based setup module.
Based on the example at https://github.com/pypa/sampleproject/blob/master/setup.py
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath( path.dirname( __file__ ) )

# Read long description from the github README.md file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name = "soffit",
    version = "0.0.1",
    
    description = "A simple-to-use graph gammar engine",
    long_description = long_description,
    long_description_content_type = "text/markdown",

    packages = find_packages(),
    install_requires = ['pyparsing','ortools'],

    url = "https://github.com/mgritter/soffit",
    author = "Mark Gritter",
    author_email = "mgritter@gmail.com",
    license = "Apache",

    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Mathematics"
    ]
)
