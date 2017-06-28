import unittest
import galsim
import galsim_extra
from astropy.io import fits
import numpy as np

class TestFitsNoise(unittest.TestCase):
    def setUp(self):
        #change this to test on a different machine
        self.fitsdir = "/Users/adamwheeler/Dropbox/y1_test"
        self.fitsfile = "DECam_00241238_01.fits"
        self.bkgfile = "DECam_00241238_01_bkg.fits"

        self.hdus = fits.open(self.fitsdir + '/' + self.fitsfile)
        self.hdus.verify('silentfix')

        #basic config file for test cases to build off of
        self.config = {}
        self.config['modules'] = ['galsim_extra']
        self.config['gal'] = {'type': 'Gaussian', 
                              'sigma': 1, 
                              'flux': 0}
        self.config['image'] = {'type': 'Single', 
                                'xsize': 2048, 
                                'ysize': 4096,
                                'pixel_scale': 0.3, 
                                'random_seed': 123}

        self.image = galsim.image.Image(2048,4096,scale=0.3,dtype=float)
        self.rng = galsim.BaseDeviate(124)


    def tearDown(self):
        self.hdus.close()

    def assertImEqual(self, im1, im2):
        np.testing.assert_array_almost_equal(im1.array, im2.array, decimal=2)

    def test_just_noise(self):
        self.config['image']['noise'] = \
            {'type': 'FitsNoise',
             'dir': self.fitsdir,
             'file_name': self.fitsfile,
             'hdu': 2}
        image = galsim.config.BuildImage(self.config)

        varmap = 1.0/self.hdus[2].data
        varimage = galsim.image.Image(varmap)
        noise = galsim.noise.VariableGaussianNoise(self.rng, varimage)
        self.image.addNoise(noise)
        self.assertImEqual(image, self.image)
            
    def test_noise_and_background(self):
        self.config['image']['noise'] = \
            {'type': 'FitsNoise',
             'dir': self.fitsdir,
             'file_name': self.fitsfile,
             'hdu': 2,
             'bkg_file_name': self.bkgfile,
             'bkg_hdu': 0}
        image = galsim.config.BuildImage(self.config)

        varmap = 1.0/self.hdus[2].data
        varimage = galsim.image.Image(varmap)
        noise = galsim.noise.VariableGaussianNoise(self.rng, varimage)
        self.image.addNoise(noise)

        hdus = fits.open(self.fitsdir + '/' + self.bkgfile)
        hdus.verify('silentfix')
        self.image += galsim.image.Image(hdus[0].data)

        self.assertImEqual(image, self.image)

if __name__ == '__main__':
    unittest.main()
