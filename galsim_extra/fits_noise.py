import galsim
from astropy.io import fits

class FitsNoiseBuilder(galsim.config.NoiseBuilder):
    def addNoise(self, config, base, im, rng, current_var, draw_method, logger):
        """
        @param config           The configuration dict for the noise field.
        @param base             The base configuration dict.
        @param im               The image onto which to add the noise
        @param rng              The random number generator to use for adding the noise.
        @param current_var      The current noise variance present in the image already [default: 0]
        @param logger           If given, a logger object to log progress.
        """
        var = self.getNoiseVariance(config, base)
        noise = galsim.noise.VariableGaussianNoise(rng, var)
        noise.applyTo(im)


    def getNoiseVariance(self, config, base):
        hdus = fits.open(config['filename'])
        hdu = hdus[config['hdu']]
        hdu.verify('fix')
        varmap = 1.0/hdu.data
        wcs = base['wcs']
        return galsim.image.Image(varmap, wcs=wcs)

galsim.config.RegisterNoiseType('FitsNoise', FitsNoiseBuilder())
