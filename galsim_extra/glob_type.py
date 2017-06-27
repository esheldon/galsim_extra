# This file defines two value types that use the `glob` package in python (akin to
# using * or ? in bash or csh).
#
# * NGlob is an integer value type that returns the number of files matching a given
#         glob pattern.
# * Glob is a string value type that returns (sequentially) the file names matching
#        a given glob pattern.
#
# Note: This is similar using the all_files input type (cf. all_files.py), but it does
#       not require an input object.  Normally all_files will be more efficient, since
#       if only requires file I/O once, but there are some situations where these
#       types may be more convenient.
#
# Also note: the file name is glob_type.py, rather than glob.py, because even with the
# absolute_import bit, I was still finding that it didn't really import correctly with
# the same name as the normal glob package.

from __future__ import absolute_import
import glob
import os
import galsim

def NGlob(config, base, value_type):
    req = { 'files': str }
    opt = { 'dir': str }
    params, safe = galsim.config.GetAllParams(config, base, req=req, opt=opt)

    dir = params.get('dir', '')  # If no dir given, joining '' will be a no op.
    files = params['files']
    files = os.path.join(dir,files)
    n = len(glob.glob(files))
    return n, safe

def Glob(config, base, value_type):
    req = { 'files': str }
    opt = { 'dir': str }
    params, safe = galsim.config.GetAllParams(config, base, req=req, opt=opt)

    dir = params.get('dir', '')  # If no dir given, joining '' will be a no op.
    files = params['files']
    files = os.path.join(dir,files)
    all_files = sorted(glob.glob(files))
    index, index_key = galsim.config.GetIndex(config, base)
    index = index % len(all_files)
    return all_files[index]


galsim.config.RegisterValueType('NGlob', NGlob, [int])
galsim.config.RegisterValueType('Glob', Glob, [str])
