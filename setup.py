import os
from setuptools import setup, find_packages

__version__ = None
pth = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "galsim_extra",
    "_version.py")
with open(pth, 'r') as fp:
    exec(fp.read())

setup(
    name="galsim_extra",
    packages=find_packages(),
    version=__version__,
)
