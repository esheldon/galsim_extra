import galsim

class PostOpStampBuilder(galsim.config.StampBuilder):

    def setup(self, config, base, xsize, ysize, ignore, logger):
        ignore = ignore + [
            'dilate', 'dilation', 'ellip', 'rotate', 'rotation', 'scale_flux',
            'magnify', 'magnification', 'shear', 'shift' ]
        return super(self.__class__,self).setup(config,base,xsize,ysize,ignore,logger)

    def buildProfile(self, config, base, psf, gsparams, logger):
        gal = galsim.config.BuildGSObject(base, 'gal', gsparams=gsparams, logger=logger)[0]

        # This line is the change from the normal StampBuilder
        psf, safe = galsim.config.gsobject.TransformObject(psf, config, base, logger)

        if psf:
            if gal:
                return galsim.Convolve(gal,psf)
            else:
                return psf
        else:
            if gal:
                return gal
            else:
                return None

galsim.config.stamp.RegisterStampType('PostOp', PostOpStampBuilder())
