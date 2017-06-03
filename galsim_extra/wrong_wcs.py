#
# This module is a very simple modification of the normal Scattered image type.
# After building the image the normal way, just before it writes out the image to disk,
# it slaps on a different wcs.

import galsim

class WrongWCSBuilder(galsim.config.image_scattered.ScatteredImageBuilder):

    def setup(self, config, base, image_num, obj_num, ignore, logger):
        ignore = ignore + ['output_wcs']
        return super(WrongWCSBuilder, self).setup(config, base, image_num, obj_num, ignore, logger)

    def buildImage(self, config, base, image_num, obj_num, logger):
        im, cv = super(WrongWCSBuilder, self).buildImage(config, base, image_num, obj_num, logger)
        output_wcs = galsim.config.BuildWCS(config, 'output_wcs', base, logger)
        base['true_wcs'] = im.wcs
        base['wcs'] = output_wcs
        return im, cv

    def addNoise(self, image, config, base, image_num, obj_num, current_var, logger):
        # This is the last thing done to the image.  So after the noise is added, update the wcs.
        output_wcs = base['wcs']
        base['wcs'] = base['true_wcs']
        super(WrongWCSBuilder, self).addNoise(image, config, base, image_num, obj_num,
                                              current_var, logger)
        base['wcs'] = output_wcs
        image.wcs = output_wcs

galsim.config.RegisterImageType('WrongWCS', WrongWCSBuilder())
