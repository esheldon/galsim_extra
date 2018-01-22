from __future__ import print_function
import galsim
import logging
import numpy as np
import os, sys
import copy
import fitsio

BASE_CONFIG={
        'modules' : ["galsim_extra","des"],

        'gal' : { 'type' : 'Sersic',
                  'n' : 1.3,
                  'shear' : { 'type' : 'G1G2', 'g1' : 0.1, 'g2' : 0. },
                },

        'psf' : { 'type' : 'Moffat', 'beta' : 2.9, 'fwhm' : 0.7 },
        'image' : { 'pixel_scale' : 0.26,
                    'size' : 48, 'random_seed' : 1234},
        'output' : { 'type' : 'MultiFits',
                     'nimages' : 10000,
                    'file_name' : "_multigaussian_test",
                    'truth': {'file_name' : "_truth_multigaussian_test.fits",
                               'columns' : {'num' : 'obj_num', 'hlr':'$(@gal.half_light_radius)',
                                            'flux' : '$(@gal.flux)'}}
                   }
    }

def test_values():
    """Test whether generated values are consistent with inputs.
    This could be tested without actually drawing images...but not sure how to do that.
    """
    #multigaussian parameters
    means = [[2.,100.], [10.,500.]]
    covs = [[0.5, 1., 20.], [0.5, 2., 20.]]
    amps = [2.,1.]
    n_obj = 100

    config = galsim.config.CopyConfig(BASE_CONFIG)
    config['input'] = {'multigaussian_sampler' : { 'amplitudes' : amps,
                                                   'means' : means,
                                                   'covs' : covs } }
    config['gal']['half_light_radius'] = {'type' : 'MultiGaussianValue', 'item_num' : 0}
    config['gal']['flux'] = {'type' : 'MultiGaussianValue', 'item_num' : 1}

    logging.basicConfig(format="%(message)s", level=logging.WARN, stream=sys.stdout)
    logger = logging.getLogger('test_multigaussian_values')
    config['rng'] = object()
    galsim.config.Process(config, logger=logger)
    #read truth
    truth_data = fitsio.read(config['output']['truth']['file_name'])

    #test amplitudes
    hlr_threshold = 6.
    flux_threshold = 300.
    nobj=len(truth_data)
    hlr_comp1_frac = float(np.sum(truth_data['hlr']<hlr_threshold))/nobj
    flux_comp1_frac = float(np.sum(truth_data['flux']<flux_threshold))/nobj
    target_frac = amps[0]/(amps[0]+amps[1])
    np.testing.assert_almost_equal( hlr_comp1_frac, target_frac, decimal=2)
    np.testing.assert_almost_equal( hlr_comp1_frac, target_frac, decimal=2)

    #test covs
    in_component_0 = truth_data['hlr']<hlr_threshold
    def get_cov(arr1, arr2):
        return np.mean( (arr1 - arr1.mean()) * (arr2 - arr2.mean()) )
    cov_hlr_flux = get_cov( truth_data['hlr'][in_component_0], truth_data['flux'][in_component_0] )
    np.testing.assert_almost_equal( cov_hlr_flux, covs[0][1], decimal=2)

if __name__ == "__main__":
    test_values()