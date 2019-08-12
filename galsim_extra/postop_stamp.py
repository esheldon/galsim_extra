import galsim

from galsim.config import StampBuilder
from galsim.config.stamp_ring import RingBuilder
from galsim.config.gsobject import TransformObject
from galsim.config.stamp import RegisterStampType

class PostOpStampBuilder(StampBuilder):

    def setup(self, config, base, xsize, ysize, ignore, logger):
        ignore = ignore + [
            'dilate', 'dilation', 'ellip', 'rotate', 'rotation', 'scale_flux',
            'magnify', 'magnification', 'shear', 'shift' ]
        return super(PostOpStampBuilder,self).setup(config,base,xsize,ysize,ignore,logger)

    def buildProfile(self, config, base, psf, gsparams, logger):
        # Change the psf appropriately
        psf, safe = TransformObject(psf, config, base, logger)
        # Then call the normal buildProfile with the new psf object.
        return super(PostOpStampBuilder,self).buildProfile(config, base, psf, gsparams, logger)

RegisterStampType('PostOp', PostOpStampBuilder())


class RingPostOpStampBuilder(RingBuilder):
    def setup(self, config, base, xsize, ysize, ignore, logger):
        # The Ring type can also have those transformations, which refer to transformations
        # of the galaxy, not the psf.  So stick the transformations in a sub-field called
        # psf_postop.
        ignore = ignore + ['psf_postop']
        return super(RingPostOpStampBuilder,self).setup(config,base,xsize,ysize,ignore,logger)

    def buildProfile(self, config, base, psf, gsparams, logger):
        if 'psf_postop' in config:
            psf, safe = TransformObject(psf, config['psf_postop'], base, logger)
        return super(RingPostOpStampBuilder,self).buildProfile(config, base, psf, gsparams, logger)

RegisterStampType('RingPostOp', RingPostOpStampBuilder())
