from __future__ import print_function
import galsim
import logging
import numpy as np
import os, sys, time

def test_wide():

    # Start by running focal_quick, but changing the image type to "WideScattered"

    config = galsim.config.ReadConfig('focal_quick.yaml')[0]
    config['image']['type'] = 'WideScattered'
    config['output']['file_name']['format'] = "widesim1_%s_%02d.fits.fz"
    config['output']['truth']['file_name']['format'] = "widetruth1_%s_%02d.dat"

    # The image.world_pos doesn't actually record the right thing in WideScattered.
    # The stamp.world_pos is where the correct ra, dec are stored for each object.
    config['output']['truth']['columns']['ra'] = "$(@stamp.world_pos).ra.deg"
    config['output']['truth']['columns']['dec'] = "$(@stamp.world_pos).dec.deg"

    logger = logging.getLogger('test_wide')
    logger.addHandler(logging.StreamHandler(sys.stdout))
    if __name__ == '__main__':
        logger.setLevel(logging.DEBUG)
    else:
        del config['image']['sky_level']  # These are the slowest bits, so remove them to`
        del config['image']['noise']      # speed up the tests when run on travis.

    t0 = time.time()
    galsim.config.Process(config, logger=logger, except_abort=True)
    t1 = time.time()
    print('Done Wide processing: t = ',t1-t0)

    # I couldn't figure out a nice way to compare the above to an equivalent non-Wide run,
    # since the random number generators are used differently and get into different states
    # in the two cases.  So for now, just check that the number of objects in each case comes
    # out right.  This is specific to this particular seed value.
    cats = [ galsim.Catalog('output/widetruth1_DECam_exp%d_%02d.dat'%(i+1,j+1))
             for i in range(2) for j in range(2) ]
    print([cat.nobjects for cat in cats])
    assert cats[0].nobjects == 5   # The first exposures gets nobjects = 12, split over 2 chips
    assert cats[1].nobjects == 7
    assert cats[2].nobjects == 13  # The second exposure gets nobjects = 19, split over 2 chips
    assert cats[3].nobjects == 6

def test_wide_nonrandom():
    # The random world_pos is what makes it hard to test the comparison between WideScattered
    # and Scattered.  So run a version that gets the ra, dec from a pre-determined list of
    # positions.
    # Also run these with a much larger area so the tests in Wide make a bigger difference.

    # Generate random ra, dec
    nobj = 2000
    ud = galsim.UniformDeviate(1234)
    ra = np.empty(nobj)
    dec = np.empty(nobj)
    ud.generate(ra)
    ud.generate(dec)

    # Range = 1 degree in each direction, centered at 19.3h, -33.1d
    ra *= 2
    ra += 19.3 * 15. - 1
    dec *= 2
    dec += -33.1 - 1

    # First run the regular Scattered, but have the input positions be from a much larger area.
    config = galsim.config.ReadConfig('focal_quick.yaml')[0]
    config['output']['file_name']['format'] = "widesim2_%s_%02d.fits.fz"
    config['output']['truth']['file_name']['format'] = "widetruth2_%s_%02d.fits"

    config['image']['world_pos']['ra'] = {
        'type' : 'Deg',
        'theta' : { 'type' : 'List', 'items' : ra }
    }
    config['image']['world_pos']['dec'] = {
        'type' : 'Deg',
        'theta' : { 'type' : 'List', 'items' : dec }
    }
    config['image']['nobjects'] = nobj

    del config['image']['sky_level']  # These are the slowest bits, so remove them to speed up this
    del config['image']['noise']      # and accentuate the difference we are looking for.

    config1 = galsim.config.CopyConfig(config)

    logger = logging.getLogger('test_wide')
    logger.addHandler(logging.StreamHandler(sys.stdout))
    #logger.setLevel(logging.DEBUG)

    t0 = time.time()
    galsim.config.Process(config1, logger=logger, except_abort=True)
    t1 = time.time()
    print('Done normal Scattered processing: t = ',t1-t0)

    # Repeat with WideScattered, but use the truth catalog rather than random numbers.
    config['image']['type'] = 'WideScattered'
    config['output']['file_name']['format'] = "widesim3_%s_%02d.fits.fz"
    config['output']['truth']['file_name']['format'] = "widetruth3_%s_%02d.fits"
    config['output']['truth']['columns']['ra'] = "$(@stamp.world_pos).ra.deg"
    config['output']['truth']['columns']['dec'] = "$(@stamp.world_pos).dec.deg"

    t2 = time.time()
    galsim.config.Process(config, logger=logger, except_abort=True)
    t3 = time.time()
    print('Done WideScattered processing: t = ',t3-t2)

    for i in range(1,3):
        for j in range(1,3):
            im1 = galsim.fits.read('output/widesim2_DECam_exp%d_%02d.fits.fz'%(i,j))
            im2 = galsim.fits.read('output/widesim3_DECam_exp%d_%02d.fits.fz'%(i,j))
            np.testing.assert_equal(im1.array, im2.array)

            cat1 = galsim.Catalog('output/widetruth2_DECam_exp%d_%02d.fits'%(i,j))
            cat2 = galsim.Catalog('output/widetruth3_DECam_exp%d_%02d.fits'%(i,j))
            assert cat1.nobjects == cat2.nobjects
            assert cat1.ncols == cat2.ncols
            assert cat1.names == cat2.names
            np.testing.assert_equal(cat1.data, cat2.data)


if __name__ == '__main__':
    test_wide()
    test_wide_nonrandom()
