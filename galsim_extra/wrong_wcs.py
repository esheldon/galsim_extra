#
# This module is a very simple modification of the normal Scattered image type.
# After building the image the normal way, just before it writes out the image to disk,
# it slaps on a different wcs.

import galsim

class WrongWCSBuilder(galsim.config.image_scattered.ScatteredImageBuilder):

    def setup(self, config, base, image_num, obj_num, ignore, logger):
        ignore = ignore + ['output_wcs']
        return super(WrongWCSBuilder, self).setup(config, base, image_num, obj_num, ignore, logger)

    def addNoise(self, image, config, base, image_num, obj_num, current_var, logger):
        # This is the last thing done to the image.  So after the noise is added, update the wcs.
        super(WrongWCSBuilder, self).addNoise(image, config, base, image_num, obj_num,
                                              current_var, logger)
        output_wcs = galsim.config.BuildWCS(config, 'output_wcs', base, logger)
        image.wcs = output_wcs

galsim.config.RegisterImageType('WrongWCS', WrongWCSBuilder())
