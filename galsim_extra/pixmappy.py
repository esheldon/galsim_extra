from __future__ import absolute_import

import galsim
import os
import pixmappy

class PixmappyBuilder(galsim.config.WCSBuilder):

    def buildWCS(self, config, base, logger):

        req = { "file_name" : str,
                "exp" : str,
                "ccdnum" : int
              }
        opt = { "dir" : str }
        kwargs, safe = galsim.config.GetAllParams(config, base, req=req, opt=opt)

        # In pixmappy, the class is GalSimWCS.  We reverse this and call it Pixmappy in the
        # config file.
        logger.info('Loading WCS for %s ccd %s',kwargs['exp'],kwargs['ccdnum'])
        wcs = pixmappy.GalSimWCS(**kwargs)
        logger.info('Done loading pixmappy WCS')

        wcs._color = 0  # For now.  Maybe make this settable somehow.
        return wcs

# Register this with GalSim:
galsim.config.RegisterWCSType('Pixmappy', PixmappyBuilder())
