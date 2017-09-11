
import galsim
import os
import numpy as np

from galsim.config.output import OutputBuilder

class FocalPlaneBuilder(OutputBuilder):
    """Implements the FocalPlane custom output type.

    This type models a full focal plane including multiple CCD images using coherent patterns
    for things like the PSF and sky level.

    The wcs is taken from a reference wcs (e.g. from a set of Fits files), but can reset the
    pointing position to a different location on the sky.
    """

    def getNFiles(self, config, base):
        """Returns the number of files to be built.

        As far as the config processing is concerned, this is the number of times it needs
        to call buildImages, regardless of how many physical files are actually written to
        disk.  So this corresponds to output.nexp for the FocalPlane output type.

        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.

        @returns the number of "files" to build.
        """
        # This is the first function from the OutputBuilder that gets called, so this is the
        # earliest that we get add this to the list of valid index keys.
        if 'exp_num' not in galsim.config.process.valid_index_keys:
            galsim.config.process.valid_index_keys += ['exp_num']
        if 'nexp' in config:
            try:
                return galsim.config.ParseValue(config, 'nexp', base, int)[0]
            except:
                galsim.config.ProcessInput(base, safe_only=True)
                return galsim.config.ParseValue(config, 'nexp', base, int)[0]
        else:
            return 1

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
        req = { 'nchips' : int, }
        opt = { 'nexp' : int, }
        ignore += [ 'file_name', 'dir' ]

        kwargs, safe = galsim.config.GetAllParams(config, base, req=req, opt=opt, ignore=ignore)

        nchips = kwargs['nchips']
        nexp = kwargs.get('nexp',1)

        if 'eval_variables' not in base:
            base['eval_variables'] = {}
        base['eval_variables']['iexp_num'] = file_num

        # Get the celestial coordinates of all the chip corners
        corners = []
        for chip_num in range(nchips):
            # Set the chip num in case needed for parsing values.
            base['eval_variables']['ichip_num'] = chip_num
            base['image_num'] = image_num + chip_num
            base['file_num'] = file_num + chip_num

            wcs = galsim.config.wcs.BuildWCS(base['image'],'wcs', base, logger)
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
        base['image_num'] = image_num  # Get back to first image_num, file_num
        base['file_num'] = file_num

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
        base['eval_variables']['ichip_num'] = '$image_num - first_image_num'
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

        # Set the random numbers to repeat for the objects so we get the same objects in the field
        # each time.
        rs = base['image']['random_seed']
        if not isinstance(rs,list):
            nobjects = galsim.config.GetCurrentValue('image.nobjects', base, int)
            first = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['image']['random_seed'] = [
                {  # Used for most things.  Repeats for each chip.
                    'type' : 'Eval',
                    'str' : 'first_seed + obj_num % @image.nobjects',
                    'ifirst_seed' : '$%d + file_num * @image.nobjects'%first
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

        # We let GalSim do its normal BuildFiles thing now, which would run in parallel
        # if appropriate.  And it writes each image to disk as it gets made rather than holding
        # the full exposure in memory before writing anything.  So copy over the current
        # config into a new dict and make appropriate adjustments to make it work.
        simple_config = {}
        simple_config.update(config)
        simple_config['nfiles'] = config['nchips']
        simple_config['type'] = 'Fits'
        base['output'] = simple_config
        if 'nproc' in base['image']:
            simple_config['nproc'] = base['image']['nproc']
        base['exp_num'] = base['file_num']

        if 'nexp' not in galsim.config.output.output_ignore:
            galsim.config.output.output_ignore += ['nexp', 'nchips']

        galsim.config.BuildFiles(nchips, base, file_num, logger=logger)

        # Go back to the original dict.
        base['output'] = config

        # The calling function is expecting to get some images to write.  Give it something
        # to avoid errors, but we won't write these.
        return [galsim.Image()] * nchips

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
        # Typically, the filename will depend on the chip_num, but if this gets called before
        # buildImages, then it won't be ready, so just check.
        if 'eval_variables' not in base:
            base['eval_variables'] = {}
        if 'ichip_num' not in base['eval_variables']:
            base['eval_variables']['ichip_num'] = 0
        if 'iexp_num' not in base['eval_variables']:
            base['eval_variables']['iexp_num'] = base['file_num']
        if 'exp_num' not in base:
            base['exp_num'] = base['file_num']
        return super(FocalPlaneBuilder, self).getFilename(config, base, logger)

    def writeFile(self, data, file_name, config, base, logger):
        """Write the data to a file.

        @param data             The data to write.  Usually a list of images returned by
                                buildImages, but possibly with extra HDUs tacked onto the end
                                from the extra output items.
        @param file_name        The file_name to write to.
        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.
        @param logger           If given, a logger object to log progress.
        """
        # These were already written during the BuildImages call, so don't do anything here.
        return

    def getNImages(self, config, base, file_num):
        """
        Get the number of images for a FocalPlane output type.

        @param config           The configuration dict for the output field.
        @param base             The base configuration dict.
        @param file_num         The current file number.

        @returns the number of images
        """
        if 'nchips' not in config:
            raise AttributeError("Attribute output.nchips is required for output.type = FocalPlane")
        return galsim.config.ParseValue(config,'nchips',base,int)[0]

    # Both of these steps will already have been done by the Fits builder.  Don't do anything here.
    def addExtraOutputHDUs(self, config, data, logger):
        return data

    def writeExtraOutputs(self, config, data, logger):
        pass

galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('FocalPlane', FocalPlaneBuilder())
