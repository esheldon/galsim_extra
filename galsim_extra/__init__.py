from __future__ import absolute_import
import glob, os

d = os.path.dirname(__file__)
files = glob.glob(os.path.join(d,'*.py'))
for f in files:
    module = os.path.basename(f)
    module = module.replace('.py','')
    if module != '__init__':
        exec("from . import "+module)

from ._version import __version__
