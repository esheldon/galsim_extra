"""
requires ngmix, scipy, scikit-learn
"""
from __future__ import print_function
import galsim
import numpy

def GenGMixND(config, base, value_type):
    """
    Generate a random number from a gaussian mixture

    the input values are for a gaussian mixture describing the
    distribution of log(flux)
    """
    from math import exp
    import ngmix

    if 'rng' not in base:
        raise ValueError("No base['rng'] available for type = LogNormal")

    rng = base['rng']

    seed=rng.raw()

    numpy_rng = numpy.random.RandomState(seed=seed)

    req = {
        'weights': list,
        'means': list,
        'covars': list,
    }
    params, safe = galsim.config.GetAllParams(config, base, req=req)

    gm = ngmix.gmix.GMixND(
        weights=params['weights'],
        means=params['means'],
        covars=params['covars'],
        rng=numpy_rng,
    )

    value=gm.sample()

    islog = base.get('islog',False)
    islog10 = base.get('islog10',False)
    if islog:
        print("converting to linear from log")
        value = exp(value)
    elif islog10:
        print("converting to linear from log10")
        value = 10.0**value

    return value, False

galsim.config.RegisterValueType('GMixND', GenGMixND, [ float ])
