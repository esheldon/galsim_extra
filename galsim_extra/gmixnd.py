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
    opt={
        'islog':bool,
        'islog10':bool,
    }
    params, safe = galsim.config.GetAllParams(
        config,
        base,
        req=req,
        opt=opt,
    )

    weights=numpy.array(params['weights'])
    means=numpy.array(params['means'])
    covars=numpy.array(params['covars'])

    gm = ngmix.gmix.GMixND(
        weights=weights,
        means=means,
        covars=covars,
        rng=numpy_rng,
    )

    value=gm.sample()

    islog = params.get('islog',False)
    islog10 = params.get('islog10',False)
    if islog:
        value = exp(value)
    elif islog10:
        value = 10.0**value

    return value, False

galsim.config.RegisterValueType('GMixND', GenGMixND, [ float ])
