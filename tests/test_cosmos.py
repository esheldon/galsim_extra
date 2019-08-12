from __future__ import print_function
import galsim
import logging
import numpy as np
import os, sys
import copy

BASE_CONFIG={
        'modules' : ["galsim_extra","des"],

        'gal' : { 'type' : 'Sersic',
                  'n' : 1.3,
                  'half_light_radius' : {'type': 'CosmosR50'},
                  'flux' : {'type' : 'CosmosFlux'},
                  'shear' : { 'type' : 'G1G2', 'g1' : 0.1, 'g2' : 0. },
                },

        'psf' : { 'type' : 'Moffat', 'beta' : 2.9, 'fwhm' : 0.7 },
        'image' : { 'pixel_scale' : 0.26,
                    'size' : 48, 'random_seed' : 1234},
        'output' : { 'type' : 'MEDS',
                     'nobjects' : 100,
                     'nfiles' : 1,
                     'nstamps_per_object' : 1,
                     'file_name' : "output/meds_%d.fits"%0,
                     'truth': {'file_name' : "output/truth_%d.dat"%0,
                               'columns' : {'num': 'obj_num', 'hlr':'$(@gal.half_light_radius)'}}
                   },
        'input' : { 'cosmos_sampler' : { 'min_r50' : 0.15, 'max_r50' : 1., 'min_flux' : 2.5, 'max_flux' : 100 }}
    }

def test_nproc():
    """
    Run BASE_CONFIG with nfiles=2 and output.nproc=-1 to test multiprocessing
    """
    config = galsim.config.CopyConfig(BASE_CONFIG)
    config['output']['nfiles']=2
    config['output']['nproc']=-1

    import logging
    logging.basicConfig(format="%(message)s", level=logging.WARN, stream=sys.stdout)
    logger = logging.getLogger('test_cosmos_nproc')
    #logger.setLevel(logging.DEBUG)
    galsim.config.Process(config, logger=logger)

def test_truth():
    """This test checks whether running the same config twice produces the same cosmos 
    sampler properties
    """
    # The config dict to write some images to a MEDS file
    i_run = 0
    seed = 1234
    pixel_scale = 0.26
    g1,g2 = 0.01, 0.
    stamp_size=32
    nobj=100
    n_per_obj=1
    nfiles = 2

    config = galsim.config.CopyConfig(BASE_CONFIG)
    #make a copy of the dict to run first
    config_0 = copy.deepcopy(config)
    import logging
    logging.basicConfig(format="%(message)s", level=logging.WARN, stream=sys.stdout)
    logger = logging.getLogger('test_cosmos_truth')
    galsim.config.Process(config_0, logger=logger)

    #Read truth data
    truth_data_0 = np.loadtxt(config_0['output']['truth']['file_name'])

    #Now run the original config after changing the truth file_name
    i_run=1
    config['output']['truth']['file_name'] = "output/truth_%d.dat"%i_run
    galsim.config.Process(config, logger=logger)
    truth_data_1 = np.loadtxt(config['output']['truth']['file_name'])
    np.testing.assert_array_equal(truth_data_0, truth_data_1)


if __name__ == "__main__":
    test_nproc()
    test_truth()

