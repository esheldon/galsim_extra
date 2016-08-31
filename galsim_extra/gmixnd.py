"""
requires ngmix, scipy, scikit-learn
"""
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
    )

    log_value=gm.sample()

    value = exp(log_value)

    return value, False

galsim.config.RegisterValueType('GMixND', GenGMixND, [ float ])
