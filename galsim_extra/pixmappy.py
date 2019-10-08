from __future__ import absolute_import

import galsim
import os
try:
    import pixmappy
except:
    pass  # Don't fail immediately if pixmappy isn't available.  Only fail it they try to use
          # the Pixmappy WCS type and `import pixmappy` doesn't work.

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
if 'Pixmappy' not in galsim.config.wcs.valid_wcs_types:
    galsim.config.RegisterWCSType('Pixmappy', PixmappyBuilder())
