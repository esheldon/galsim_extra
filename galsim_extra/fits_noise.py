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
        req = {'hdu': int, 'dir': str, 'file_name': str}
        opt = {'dir': str}
        params, safe = galsim.config.GetAllParams(config, base, req=req, opt=opt)        


        filename = params.get('dir', '.') + '/' + params['file_name']

        hdus = fits.open(filename)
        hdu = hdus[params['hdu']]
        hdu.verify('silentfix')

        varmap = 1.0/hdu.data

        #set any negative vars to 0
        varmap[varmap < 0] = 0

        wcs = base['wcs'] #does this need to be interpretted by galsim somehow?
        return galsim.image.Image(varmap, wcs=wcs)

galsim.config.RegisterNoiseType('FitsNoise', FitsNoiseBuilder())
