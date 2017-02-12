import galsim

class PostOpStampBuilder(galsim.config.StampBuilder):

    def setup(self, config, base, xsize, ysize, ignore, logger):
        ignore = ignore + [
            'dilate', 'dilation', 'ellip', 'rotate', 'rotation', 'scale_flux',
            'magnify', 'magnification', 'shear', 'shift' ]
        return super(self.__class__,self).setup(config,base,xsize,ysize,ignore,logger)

    def buildProfile(self, config, base, psf, gsparams, logger):
        obj = super(self.__class__,self).buildProfile(config, base, psf, gsparams, logger)
        obj, safe = galsim.config.gsobject.TransformObject(obj, config, base, logger)
        return obj

galsim.config.stamp.RegisterStampType('PostOp', PostOpStampBuilder())
