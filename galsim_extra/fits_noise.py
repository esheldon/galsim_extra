import galsim
from astropy.io import fits

class FitsNoiseBuilder(galsim.config.NoiseBuilder):
    req = {'hdu': int, 'file_name': str}
    opt = {'dir': str, 'bkg_hdu': int, 'bkg_dir': str, 'bkg_file_name': str}
    
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
        im.addNoise(noise)

        #add background if applicable
        params, safe = galsim.config.GetAllParams(config, base, req=self.req, opt=self.opt)
        if 'bkg_hdu' in params:
            filename = params.get('bkg_file_name', params['file_name'])
            directory = params.get('bkg_dir', params.get('dir', '.'))
            path = directory + '/' + filename

            hdus = fits.open(path)
            hdu = hdus[params['bkg_hdu']]
            hdu.verify('silentfix')

            im += galsim.image.Image(hdu.data)


    def getNoiseVariance(self, config, base):
        params, safe = galsim.config.GetAllParams(config, base, req=self.req, opt=self.opt)        

        filename = params.get('dir', '.') + '/' + params['file_name']

        hdus = fits.open(filename)
        hdu = hdus[params['hdu']]
        hdu.verify('silentfix')

        varmap = 1.0/hdu.data

        #wcs = base['wcs'] #does this need to be interpretted by galsim somehow?
        return galsim.image.Image(varmap, wcs=None)


galsim.config.RegisterNoiseType('FitsNoise', FitsNoiseBuilder())
