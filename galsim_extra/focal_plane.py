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
    def setup(self, config, base, file_num, logger):
        logger.debug('Start FocalPlaneBuilder setup file_num=%d', file_num)
        # Make sure exp_num is considered a valid index_key.
        if 'exp_num' not in galsim.config.process.valid_index_keys:
            galsim.config.valid_index_keys += ['exp_num', 'chip_num']
            galsim.config.eval_base_variables += ['exp_num', 'chip_num', 'exp_start_obj_num']

        if 'nexp' in config:
            # Sometimes this will be called prior to ProcessInput being called, so if there is an
            # error, try loading the inputs and then try again.
            try:
                nexp = galsim.config.ParseValue(config, 'nexp', base, int)[0]
            except:
                galsim.config.ProcessInput(base, safe_only=True)
                nexp = galsim.config.ParseValue(config, 'nexp', base, int)[0]
        else:
            nexp = 1

        # We'll be setting the random number seed to repeat for each chip, which requires
        # querying the number of objects in the exposure.  This however leads to a logical
        # infinite loop if the number of objects is a random variate.  So to make this work,
        # we first get the number of objects in each exposure using a well-defined rng, and
        # save those values to a list, which is then fully deterministic for all other uses.
        if 'nobjects' not in base['image']:
            raise ValueError("image.nobjects is required for output type 'FocalPlane'")
        nobj = base['image']['nobjects']
        if not isinstance(nobj, dict) or not nobj.get('_setup_as_list', False):
            seed = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['exp_num_rng'] = base['rng'] = galsim.BaseDeviate(seed)
            nobj_list = []
            for exp_num in range(nexp):
                base['exp_num'] = exp_num
                nobj = galsim.config.ParseValue(base['image'], 'nobjects', base, int)[0]
                nobj_list.append(nobj)
            base['image']['nobjects'] = {
                'type' : 'List',
                'items' : nobj_list,
                'index_key' : 'exp_num',
                '_setup_as_list' : True,
            }
        logger.debug('nobjects = %s', galsim.config.CleanConfig(base['image']['nobjects']))

        # Set the random numbers to repeat for the objects so we get the same objects in the field
        # each time.
        rs = base['image']['random_seed']
        if not isinstance(rs,list):
            first = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['image']['random_seed'] = []
            # The first one is the original random_seed specification, used for noise, since
            # that should be different on each chip, and probably most things in input, output,
            # or image.
            if isinstance(rs,int):
                base['image']['random_seed'].append(
                    { 'type' : 'Sequence', 'index_key' : 'obj_num', 'first' : first } )
            else:
                base['image']['random_seed'].append(rs)

            # The second one is used for the galaxies and repeats through the same set of seed
            # values for each chip in an expousre.
            base['image']['random_seed'].append(
                {
                    'type' : 'Eval',
                    'str' : 'first + exp_start_obj_num + (obj_num - exp_start_obj_num) % nobjects',
                    'ifirst' : first,
                    'inobjects' : { 'type' : 'Current', 'key' : 'image.nobjects' }
                }
            )

            # We also add a third one that will repeat for all exposures.  So could be used
            # for making galaxy properties the same in all exposures in a multi-exposure context.
            # Note: this would only work correctly if nobjects is constant.
            base['image']['random_seed'].append(
                {
                    'type' : 'Eval',
                    'str' : 'first + (obj_num - exp_start_obj_num) % nobjects',
                    'ifirst' : first,
                    'inobjects' : { 'type' : 'Current', 'key' : 'image.nobjects' }
                }
            )

            if 'gal' in base:
                base['gal']['rng_num'] = 1
            if 'stamp' in base:
                base['stamp']['rng_num'] = 1
            if 'image_pos' in base['image']:
                base['image']['image_pos']['rng_num'] = 1
            if 'world_pos' in base['image']:
                base['image']['world_pos']['rng_num'] = 1

        logger.debug('random_seed = %s', galsim.config.CleanConfig(base['image']['random_seed']))

        # Do this after the above just in case nchips has a random component.
        try:
            nchips = galsim.config.ParseValue(config, 'nchips', base, int)[0]
        except:
            galsim.config.ProcessInput(base, safe_only=True)
            nchips = galsim.config.ParseValue(config, 'nchips', base, int)[0]

        # Make sure that exp_num and chip_num are setup properly in the right places.
        exp_num = file_num // nchips
        chip_num = file_num % nchips
        base['exp_num'] = exp_num
        base['chip_num'] = chip_num
        nobjects = galsim.config.ParseValue(base['image'], 'nobjects', base, int)[0]
        base['exp_start_obj_num'] = base['start_obj_num'] - chip_num * nobjects
        logger.debug('file_num, nexp, nchips = %d, %d, %d', file_num, nexp, nchips)
        logger.debug('exp_num, chip_num = %d, %d', exp_num, chip_num)

        # This sets up the RNG seeds.
        OutputBuilder.setup(self, config, base, file_num, logger)

    def getNFiles(self, config, base):
        """Returns the number of files to be built.

        As far as the config processing is concerned, this is the number of times it needs
        to call buildImages, regardless of how many physical files are actually written to
        disk.  So this corresponds to output.nexp for the FocalPlane output type.

        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.

        @returns the number of "files" to build.
        """
        nexp = galsim.config.ParseValue(config, 'nexp', base, int)[0]
        nchips = galsim.config.ParseValue(config, 'nchips', base, int)[0]
        return nexp * nchips

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

        exp_num = base['exp_num']
        chip_num = base['chip_num']
        req = { 'nchips' : int, }
        opt = { 'nexp' : int, }
        ignore += [ 'file_name', 'dir' ]
        kwargs = galsim.config.GetAllParams(config, base, req=req, opt=opt, ignore=ignore)[0]
        nexp = kwargs.get('nexp',1)
        nchips = kwargs['nchips']
        logger.debug("nexp, nchips, expnum, chipnum = %d, %d, %d, %d",nexp,nchips,exp_num,chip_num)

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
            ra_list = [p.ra.wrap(pointing.ra) / galsim.degrees for p in corners]
            dec_list = [p.dec / galsim.degrees for p in corners]
            fov_minra = np.min(ra_list)
            fov_maxra = np.max(ra_list)
            fov_mindec = np.min(dec_list)
            fov_maxdec = np.max(dec_list)
            logger.info("RA range = %.2f - %.2f deg", fov_minra, fov_maxra)
            logger.info("Dec range = %.2f - %.2f deg", fov_mindec, fov_maxdec)

            # bounds is the bounds in the tangent plane
            proj_list = [ pointing.project(p, projection='gnomonic') for p in corners]
            # Convert Angle tuples into PositionD in arcsec
            proj_list = [ galsim.PositionD(p[0]/galsim.arcsec, p[1]/galsim.arcsec)
                            for p in proj_list ]
            bounds = galsim.BoundsD()
            for proj in proj_list: bounds += proj
            logger.info("Bounds in tangent plane = %s (arcsec)",bounds)

            # Write these values into the dict in eval_variables, so they can be used in Eval's.
            base['eval_variables']['aworld_center_ra'] = pointing.ra
            base['eval_variables']['aworld_center_dec'] = pointing.dec
            base['eval_variables']['afov_minra'] = fov_minra * galsim.degrees
            base['eval_variables']['afov_maxra'] = fov_maxra * galsim.degrees
            base['eval_variables']['afov_mindec'] = fov_mindec * galsim.degrees
            base['eval_variables']['afov_maxdec'] = fov_maxdec * galsim.degrees
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

galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('FocalPlane', FocalPlaneBuilder())
