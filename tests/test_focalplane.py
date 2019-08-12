from __future__ import print_function
import galsim
import logging
import numpy as np
import os, sys

def test_truth():
    """This test addressed Issue 10, where Niall found that the truth catalog wasn't being
    built correctly with the FocalPlane builder.
    """
    config = galsim.config.ReadConfig('focal_quick.yaml')[0]
    logger = logging.getLogger('test_truth')
    logger.addHandler(logging.StreamHandler(sys.stdout))
    if __name__ == '__main__':
        logger.setLevel(logging.DEBUG)

    galsim.config.Process(config, logger=logger, except_abort=True)

    exp_data_list = []
    for exp in range(2):
        truth_files = ['truth_DECam_exp%d_%02d.dat'%(exp+1,chip+1) for chip in range(2)]
        data_list = []
        for truth_file in truth_files:
            print(truth_file)
            data = np.genfromtxt(os.path.join('output',truth_file), names=True, dtype=None,
                                 encoding='ascii')
            print('file %s = '%truth_file, data)
            data_list.append(data)
        exp_data_list.append(data_list)

        # Within a single exposure, many properties should be identical for the galaxies.
        np.testing.assert_equal(data_list[0]['x'], data_list[1]['x'])
        np.testing.assert_equal(data_list[0]['y'], data_list[1]['y'])
        np.testing.assert_equal(data_list[0]['obj_type'], data_list[1]['obj_type'])
        np.testing.assert_equal(data_list[0]['flux'], data_list[1]['flux'])
        np.testing.assert_equal(data_list[0]['shear_g1'], data_list[1]['shear_g1'])
        np.testing.assert_equal(data_list[0]['shear_g2'], data_list[1]['shear_g2'])
        np.testing.assert_equal(data_list[0]['gal_hlr'], data_list[1]['gal_hlr'])
        np.testing.assert_equal(data_list[0]['bulge_g1'], data_list[1]['bulge_g1'])
        np.testing.assert_equal(data_list[0]['bulge_g2'], data_list[1]['bulge_g2'])
        np.testing.assert_equal(data_list[0]['disk_g1'], data_list[1]['disk_g1'])
        np.testing.assert_equal(data_list[0]['disk_g2'], data_list[1]['disk_g2'])

        # The PSF properties should not be the same though.
        assert not np.any(data_list[0]['psf_fwhm'] == data_list[1]['psf_fwhm'])
        assert not np.any(data_list[0]['psf_e1'] == data_list[1]['psf_e1'])
        assert not np.any(data_list[0]['psf_e2'] == data_list[1]['psf_e2'])

    # The number of galaxies should be different for each exposure
    n0 = len(exp_data_list[0][0])
    n1 = len(exp_data_list[1][0])
    assert n0 != n1
    np.testing.assert_array_equal(exp_data_list[0][0]['num'], range(0,n0))
    np.testing.assert_array_equal(exp_data_list[0][1]['num'], range(n0,2*n0))
    np.testing.assert_array_equal(exp_data_list[1][0]['num'], range(2*n0,2*n0+n1))
    np.testing.assert_array_equal(exp_data_list[1][1]['num'], range(2*n0+n1,2*n0+2*n1))

    # Most galaxy properties should be different for different exposures
    n = min(n0,n1)
    for key in ['x', 'y', 'flux', 'gal_hlr', 'bulge_g1', 'bulge_g2', 'disk_g1', 'disk_g2']:
        assert np.all(np.not_equal(exp_data_list[0][0][key][:n], exp_data_list[1][0][key][:n]))
    # Some won't be all different, but shouldn't be all equal either.
    for key in ['obj_type', 'obj_type_index', 'shear_g1']:
        # Note, shear_g2 is always 0, so don't include that one.
        assert not np.all(exp_data_list[0][0][key][:n] == exp_data_list[1][0][key][:n])

if __name__ == '__main__':
    test_truth()
