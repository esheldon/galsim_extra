import galsim

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
            im += galsim.fits.read(filename, dir=directory, hdu=params['bkg_hdu'])


    def getNoiseVariance(self, config, base):
        params, safe = galsim.config.GetAllParams(config, base, req=self.req, opt=self.opt)        

        filename = params['file_name']
        varimage = galsim.fits.read(filename, dir=params.get('dir',None), hdu=params['hdu'])
        varimage.invertSelf()
        return varimage


galsim.config.RegisterNoiseType('FitsNoise', FitsNoiseBuilder())
