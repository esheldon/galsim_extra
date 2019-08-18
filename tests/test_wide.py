from __future__ import print_function
import galsim
import logging
import numpy as np
import os, sys, time

def test_wide():

    # Start by running focal_quick, but changing the image type to "WideScattered"

    config = galsim.config.ReadConfig('focal_quick.yaml')[0]
    config['image']['type'] = 'WideScattered'
    config['output']['file_name']['format'] = "widesim_%s_%02d.fits.fz"
    config['output']['truth']['file_name']['format'] = "widetruth_%s_%02d.dat"

    # The image.world_pos doesn't actually record the right thing in WideScattered.
    # The stamp.world_pos is where the correct ra, dec are stored for each object.
    config['output']['truth']['columns']['ra'] = "$(@stamp.world_pos).ra.deg"
    config['output']['truth']['columns']['dec'] = "$(@stamp.world_pos).dec.deg"

    logger = logging.getLogger('test_wide')
    logger.addHandler(logging.StreamHandler(sys.stdout))
    if __name__ == '__main__':
        logger.setLevel(logging.DEBUG)
        del config['image']['sky_level']  # These are the slowest bits, so remove them to`
        del config['image']['noise']      # speed up the tests when run on travis.
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
    cats = [ galsim.Catalog('output/widetruth_DECam_exp%d_%02d.dat'%(i+1,j+1))
             for i in range(2) for j in range(2) ]
    print([cat.nobjects for cat in cats])
    assert cats[0].nobjects == 5   # The first exposures gets nobjects = 12, split over 2 chips
    assert cats[1].nobjects == 7
    assert cats[2].nobjects == 13  # The second exposure gets nobjects = 19, split over 2 chips
    assert cats[3].nobjects == 6


if __name__ == '__main__':
    test_wide()
