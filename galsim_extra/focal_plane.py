from __future__ import print_function
import galsim
import os
import numpy as np
import copy

from galsim.config.output import OutputBuilder

class FocalPlaneBuilder(OutputBuilder):
    """Implements the FocalPlane custom output type.

    This type models a full focal plane including multiple CCD images using coherent patterns
    for things like the PSF and sky level.

    The wcs is taken from a reference wcs (e.g. from a set of Fits files), but can reset the
    pointing position to a different location on the sky.
    """
    def _setup(self, config, base, file_num):
        """Do some setup that needs to happen before doing most other calculations.
        Also returns nexp, nchips for convenience.
        """
        # Make sure exp_num is considered a valid index_key.
        if 'exp_num' not in galsim.config.process.valid_index_keys:
            galsim.config.process.valid_index_keys += ['exp_num']

        # Set the random numbers to repeat for the objects so we get the same objects in the field
        # each time.
        rs = base['image']['random_seed']
        if not isinstance(rs,list):
            first = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['first_seed'] = first
            base['image']['random_seed'] = [
                {  # Used for most things.  Repeats for each chip.
                    'type' : 'Eval',
                    'str' : 'first_seed + exp_num * nobjects + obj_num % nobjects',
                    'ifirst_seed' : first,
                    'inobjects' : { 'type' : 'Current', 'key' : 'image.nobjects' }
                }
            ]
            # The second one is the original random_seed specification,  used for noise, since
            # that should be different on each chip.
            if isinstance(rs,int):
                base['image']['random_seed'].append(
                    { 'type' : 'Sequence', 'index_key' : 'obj_num', 'first' : first } )
            else:
                base['image']['random_seed'].append(rs)
            if 'noise' in base['image']:
                base['image']['noise']['rng_num'] = 1

        # Sometimes this will be called prior to ProcessInput being called, so if there is an
        # error, try loading the inputs and then try again.
        try:
            if 'nexp' in config:
                nexp = galsim.config.ParseValue(config, 'nexp', base, int)[0]
            else:
                nexp = 1
            nchips = galsim.config.ParseValue(config, 'nchips', base, int)[0]
        except:
            galsim.config.ProcessInput(base, safe_only=True)
            if 'nexp' in config:
                nexp = galsim.config.ParseValue(config, 'nexp', base, int)[0]
            else:
                nexp = 1
            nchips = galsim.config.ParseValue(config, 'nchips', base, int)[0]

        # Make sure that exp_num and chip_num are setup properly in the right places.
        exp_num = file_num // nchips
        chip_num = file_num % nchips
        base['chip_num'] = chip_num
        if 'eval_variables' not in base:
            base['eval_variables'] = {}
        base['eval_variables']['ichip_num'] = chip_num
        base['eval_variables']['iexp_num'] = exp_num

        # Make sure there is an appropriate RNG for exp_num.
        if exp_num != base.get('exp_num',None):
            base['exp_num'] = exp_num
            # Can't use the normal seed, since that depends on nobjects, which may in turn
            # require an exp_num_rng to already be set.  Use a different, arbitrary sequence.
            seed = base['first_seed'] + 314159 + exp_num * 12345
            rng = galsim.BaseDeviate(seed)
            base['exp_num_seed'] = seed
            base['exp_num_rng'] = rng
            base['exp_num_rngs'] = [rng, rng]

        return nexp, nchips

    def getNFiles(self, config, base):
        """Returns the number of files to be built.

        As far as the config processing is concerned, this is the number of times it needs
        to call buildImages, regardless of how many physical files are actually written to
        disk.  So this corresponds to output.nexp for the FocalPlane output type.

        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.

        @returns the number of "files" to build.
        """
        nexp, nchips = self._setup(config, base, 0)
        return nexp * nchips

    def getNObjPerImage(self, config, base, file_num, image_num):
        """
        Get the number of objects that will be made for each image built as part of the file
        file_num, which starts at image number image_num, based on the information in the config
        dict.

        @param config           The configuration dict.
        @param base             The base configuration dict.
        @param file_num         The current file number.
        @param image_num        The current image number (the first one for this file).

        @returns a list of the number of objects in each image [ nobj0, nobj1, nobj2, ... ]
        """
        # This just sets things up if necessary.
        self._setup(config, base, file_num)
        nobj = OutputBuilder.getNObjPerImage(self, config, base, file_num, image_num)
        return nobj

    def buildImages(self, config, base, file_num, image_num, obj_num, ignore, logger):
        """Build the images

        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.
        @param file_num         The current file_num.
        @param image_num        The current image_num.
        @param obj_num          The current obj_num.
        @param ignore           A list of parameters that are allowed to be in config that we can
                                ignore here.  i.e. it won't be an error if they are present.
        @param logger           If given, a logger object to log progress.

        @returns a list of the images built
        """
        logger.info('Starting buildImages')
        logger.info('file_num: %d'%base['file_num'])
        logger.info('image_num: %d',base['image_num'])

        nexp, nchips = self._setup(config, base, file_num)
        exp_num = base['exp_num']
        chip_num = base['chip_num']
        logger.debug("nexp, nchips, expnum, chipnum = %d, %d, %d, %d",nexp,nchips,exp_num,chip_num)

        # Just check there aren't other invalid parameters in the dict.
        req = { 'nchips' : int, }
        opt = { 'nexp' : int, }
        ignore += [ 'file_name', 'dir' ]
        galsim.config.CheckAllParams(config, req=req, opt=opt, ignore=ignore)

        # Additional setup only for the first time we get to this particular exp_num.
        if base.get('_focalplane_expnum_setup',None) != exp_num:
            logger.info('First file in the exposure.  Do some additional setup.')
            base['_focalplane_expnum_setup'] = exp_num

            # Get the celestial coordinates of all the chip corners
            corners = []
            for chip_num in range(nchips):
                wcs = galsim.config.wcs.BuildWCS(base['image'],'wcs', base, logger)
                if not wcs.isCelestial():
                    raise ValueError("FocalPlane requires a CelestialWCS")
                xsize = galsim.config.ParseValue(base['image'],'xsize', base, int)[0]
                ysize = galsim.config.ParseValue(base['image'],'ysize', base, int)[0]

                im_pos1 = galsim.PositionD(0,0)
                im_pos2 = galsim.PositionD(0,ysize)
                im_pos3 = galsim.PositionD(xsize,0)
                im_pos4 = galsim.PositionD(xsize,ysize)
                corners.append(wcs.toWorld(im_pos1))
                corners.append(wcs.toWorld(im_pos2))
                corners.append(wcs.toWorld(im_pos3))
                corners.append(wcs.toWorld(im_pos4))

            # Calculate the pointing as the center (mean) of all the position in corners
            x_list, y_list, z_list = zip(*[p.get_xyz() for p in corners])
            pointing_x = np.mean(x_list)
            pointing_y = np.mean(y_list)
            pointing_z = np.mean(z_list)
            pointing = galsim.CelestialCoord.from_xyz(pointing_x, pointing_y, pointing_z)
            logger.info("Calculated center of focal plane to be %s",pointing)

            # Also calculate the min/max ra and dec
            ra_list = [p.ra.wrap(pointing.ra) for p in corners]
            dec_list = [p.dec for p in corners]
            fov_minra = np.min(ra_list)
            fov_maxra = np.max(ra_list)
            fov_mindec = np.min(dec_list)
            fov_maxdec = np.max(dec_list)
            logger.info("RA range = %.2f - %.2f deg",
                        fov_minra/galsim.degrees, fov_maxra/galsim.degrees)
            logger.info("Dec range = %.2f - %.2f deg",
                        fov_mindec/galsim.degrees, fov_maxdec/galsim.degrees)

            # bounds is the bounds in the tangent plane
            proj_list = [ pointing.project(p, projection='gnomonic') for p in corners]
            bounds = galsim.BoundsD()
            for proj in proj_list: bounds += proj
            logger.info("Bounds in tangent plane = %s (arcsec)",bounds)

            # Write these values into the dict in eval_variables, so they can be used in Eval's.
            base['eval_variables']['aworld_center_ra'] = pointing.ra
            base['eval_variables']['aworld_center_dec'] = pointing.dec
            base['eval_variables']['afov_minra'] = fov_minra
            base['eval_variables']['afov_maxra'] = fov_maxra
            base['eval_variables']['afov_mindec'] = fov_mindec
            base['eval_variables']['afov_maxdec'] = fov_maxdec
            base['eval_variables']['ifirst_image_num'] = image_num
            base['eval_variables']['ffocal_xmin'] = bounds.xmin
            base['eval_variables']['ffocal_xmax'] = bounds.xmax
            base['eval_variables']['ffocal_ymin'] = bounds.ymin
            base['eval_variables']['ffocal_ymax'] = bounds.ymax
            rmax = np.max([proj.x**2 + proj.y**2 for proj in proj_list])**0.5
            logger.info("Max radius from center of focal plane = %.0f arcsec",rmax)
            base['eval_variables']['ffocal_rmax'] = rmax
            base['eval_variables']['xworld_center'] = pointing
            base['world_center'] = pointing
            base['eval_variables']['ffocal_r'] = {
                'type' : 'Eval',
                'str' : "math.sqrt(pos.x**2 + pos.y**2)",
                'ppos' : { 'type' : 'Eval',
                           'str' : "world_center.project(world_pos)",
                           'cworld_pos' : "@image.world_pos"
                         }
            }

        # Evaluate all the meta parameters and write them into the eval_variables dict.
        if 'meta_params' in base:
            for key in base['meta_params']:
                param = galsim.config.ParseValue(base['meta_params'], key, base, float)[0]
                base['eval_variables']['f' + key] = param
            galsim.config.RemoveCurrent(base['meta_params'])

        # Now we run the base class BuildImages, which just builds a single image.
        ignore += ['nexp', 'nchips']
        images = OutputBuilder.buildImages(self, config, base, file_num, image_num, obj_num,
                                           ignore, logger)
        return images

    def getFilename(self, config, base, logger):
        """Get the file_name for the current file being worked on.

        Note that the base class defines a default extension = '.fits'.
        This can be overridden by subclasses by changing the default_ext property.

        @param config           The configuration dict for the output type.
        @param base             The base configuration dict.
        @param ignore           A list of parameters that are allowed to be in config['output']
                                that we can ignore here.  i.e. it won't be an error if these
                                parameters are present.
        @param logger           If given, a logger object to log progress.

        @returns the filename to build.
        """
        logger.debug("Get filename for file_num = %s",base['file_num'])
        self._setup(config, base, base['file_num'])
        name = OutputBuilder.getFilename(self, config, base, logger)
        logger.debug("name = %s",name)
        return name


def clean_config(config):
    if isinstance(config, dict):
        return { k : clean_config(config[k]) for k in config if k[0] != '_' }
    elif isinstance(config, list):
        return [ clean_config(item) for item in config ]
    else:
        return config

galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('FocalPlane', FocalPlaneBuilder())
