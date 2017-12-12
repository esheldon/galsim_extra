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

    galsim.config.Process(config, logger=logger)
    
    truth_files = ['truth_DECam_exp1_01.dat', 'truth_DECam_exp1_02.dat',
                   'truth_DECam_exp2_01.dat', 'truth_DECam_exp2_02.dat']
    for truth_file in truth_files:
        print(truth_file)
        data = np.genfromtxt(os.path.join('output',truth_file), names=True)
        print('file %s = '%truth_file, data)

if __name__ == '__main__':
    test_truth()
