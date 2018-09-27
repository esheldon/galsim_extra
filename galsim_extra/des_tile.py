import galsim
import os
import numpy as np
import copy
import yaml
from galsim.config.output import OutputBuilder

class DESTileBuilder(OutputBuilder):
    """Implements the DESTile custom output type.

    This type models a full focal plane including multiple CCD images using coherent patterns
    for things like the PSF and sky level.

    The wcs is taken from a reference wcs (e.g. from a set of Fits files), but can reset the
    pointing position to a different location on the sky.
    """
    def setup(self, config, base, file_num, logger):
        logger.debug("Start DESTileBuilder setup file_num=%d"%file_num)
        
        #Make sure tile_num, band_num, exp_num, chip_num are considered valid index_keys
        if "tile_num" not in galsim.config.process.valid_index_keys:
            galsim.config.valid_index_keys += ["tile_num", "band_num", "exp_num", "chip_num"]
            galsim.config.eval_base_variables += ["tile_num", "band_num", "exp_num", "chip_num", "tile_start_obj_num", "nfiles"]

        if 'ntiles' in config:
            # Sometimes this will be called prior to ProcessInput being called, so if there is an
            # error, try loading the inputs and then try again.
            try:
                ntiles = galsim.config.ParseValue(config, 'ntiles', base, int)[0]
            except:
                galsim.config.ProcessInput(base, safe_only=True)
                ntiles = galsim.config.ParseValue(config, 'ntiles', base, int)[0]
        else:
            ntiles = 1

        # We'll be setting the random number seed to repeat for each band, which requires
        # querying the number of objects in the exposure.  This however leads to a logical
        # infinite loop if the number of objects is a random variate.  So to make this work,
        # we first get the number of objects in each exposure using a well-defined rng, and
        # save those values to a list, which is then fully deterministic for all other uses.
        if 'nobjects' not in base['image']:
            raise ValueError("image.nobjects is required for output type 'DESTileBuilder'")
        nobj = base['image']['nobjects']
        if not isinstance(nobj, dict) or not nobj.get('_setup_as_list', False):
            logger.debug("generating nobj for all tiles:")
            seed = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['tile_num_rng'] = base['rng'] = galsim.BaseDeviate(seed)
            nobj_list = []
            for tile_num in range(ntiles):
                base['tile_num'] = tile_num
                nobj = galsim.config.ParseValue(base['image'], 'nobjects', base, int)[0]
                nobj_list.append(nobj)
            base['image']['nobjects'] = {
                'type' : 'List',
                'items' : nobj_list,
                'index_key' : 'tile_num',
                '_setup_as_list' : True,
            }
        logger.debug('nobjects = %s', galsim.config.CleanConfig(base['image']['nobjects']))

        # Set the random numbers to repeat for the objects so we get the same objects in the field
        # each time. In fact what we do is generate three sets of random seeds:
        # 0 : Sequence of seeds that iterates with obj_num i.e. no repetetion. Used for noise
        # 1 : Sequence of seeds that starts with the first object number for a given tile, then iterates 
        # with the obj_num minus the first object number for that band, intended for quantities 
        # that should be the same between bands for a given tile.

        rs = base['image']['random_seed']
        if not isinstance(rs,list):
            first = galsim.config.ParseValue(base['image'], 'random_seed', base, int)[0]
            base['image']['random_seed'] = []
            # The first one is the original random_seed specification, used for noise, since
            # that should be different for each band, and probably most things in input, output,
            # or image.
            if isinstance(rs,int):
                base['image']['random_seed'].append(
                    { 'type' : 'Sequence', 'index_key' : 'obj_num', 'first' : first } )
            else:
                base['image']['random_seed'].append(rs)

            # The second one is used for the galaxies and repeats through the same set of seed
            # values for each band in a tile.
            if nobj>0:
                base['image']['random_seed'].append(
                    {
                        'type' : 'Eval',
                        'str' : 'first + tile_start_obj_num + (obj_num - tile_start_obj_num) % nobjects',
                        'ifirst' : first,
                        'inobjects' : { 'type' : 'Current', 'key' : 'image.nobjects' }
                    }
                )
            else:
                base['image']['random_seed'].append(base['image']['random_seed'][0])


            # The third iterates per tile
            base['image']['random_seed'].append(
                { 'type' : 'Sequence', 'index_key' : 'tile_num', 'first' : first } )


            if 'gal' in base:
                base['gal']['rng_num'] = 1
            if 'stamp' in base:
                base['stamp']['rng_num'] = 1
            if 'image_pos' in base['image']:
                base['image']['image_pos']['rng_num'] = 1
            if 'world_pos' in base['image']:
                base['image']['world_pos']['rng_num'] = 1
        
        logger.debug('random_seed = %s', galsim.config.CleanConfig(base['image']['random_seed']))

        #Now, if we haven't already, we need to read in some things which determine what images to simulate
        tilenames = config["tilenames"]
        ntiles = len(tilenames)
        bands = config["bands"]
        
        if "_tile_setup" not in config:
            tile_setup = {}
            tile_num_list = []  #Total number of images length list of tile number
            exp_num_list = []   #Total number of images length list of exposure number
            file_num_in_exp_list = []   #Total number of images length list of files
            band_list = []  #Total number of images length list of band
            im_file_list = []
            mag_zp_list = []
            unique_im_dirs = []
            psfex_file_list = []
            ra_ranges_deg = []
            dec_ranges_deg = []
            for tile_num,tilename in enumerate(tilenames):
                #Get single-epoch image info for this tile
                for band in bands:
                    source_list = os.path.join( os.environ["DESDATA"], tilename, "lists", "%s_%s_fcut-flist-y3v02.dat"%(tilename, band))
                    with open(source_list, "r") as f:
                        lines = f.readlines()
                    lines = [l.strip() for l in lines if l.strip()!=""] #remove empty lines
                    image_files = [l.split()[0] for l in lines]
                    #also get psfex file here
                    psfex_files = [ os.path.join(os.path.dirname(f).replace("red/immask", "psf"), 
                                                 "%s_psfexcat.psf"%( "_".join((os.path.basename(f).split("_"))[:-1]))) for f in image_files ]
                    psfex_file_list += psfex_files
                    mag_zps = [float(l.split()[1]) for l in lines]
                    im_file_list += image_files
                    mag_zp_list += mag_zps
                    im_dirs = [ os.path.dirname(f) for f in image_files ]
                    for d in im_dirs:
                        if d not in unique_im_dirs:
                            unique_im_dirs.append(d)
                    tile_num_list += [tile_num] * len(image_files)
                    band_list += band * len(image_files)

                #Also get bounds from the coadd
                tile_data_file = os.path.join( os.environ["DESDATA"], tilename, "lists", "%s_%s_fileconf-y3v02.yaml"%(tilename, band))
                with open(tile_data_file, "rb") as f:
                    tile_data = yaml.load(f)
                coadd_file = tile_data["coadd_image_url"]
                wcs = galsim.wcs.readFromFitsHeader(coadd_file)
                xmin,xmax,ymin,ymax = 1.,10000.,1.,10000.
                corners = [ wcs[0].toWorld( galsim.PositionD(a,b) ) for (a,b) in [ (xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax) ] ]
                corner_ras_deg = [ c.ra.wrap( corners[0].ra ) / galsim.degrees for c in corners ]
                corner_decs_deg = [ c.dec / galsim.degrees for c in corners ]
                ra_ranges_deg.append(( np.min(corner_ras_deg), np.max(corner_ras_deg) ))
                dec_ranges_deg.append(( np.min(corner_decs_deg), np.max(corner_decs_deg) ))
                

            config["_tile_setup"] = {}
            tile_setup = config["_tile_setup"]
            tile_setup["image_files"] = im_file_list
            tile_setup["tile_num_list"] = tile_num_list
            tile_setup["file_num_in_tile"] = [ tile_num_list[:i].count(tile_num_list[i]) for i in range(len(tile_num_list)) ]
            tile_setup["mag_zp_list"] = mag_zp_list
            tile_setup["psfex_files"] = psfex_file_list
            tile_setup["ra_ranges_deg"] = ra_ranges_deg
            tile_setup["dec_ranges_deg"] = dec_ranges_deg
            tile_setup["band_list"] = band_list

        #Random seed stuff needs tile_num and tile_start_obj_num
        tile_setup = config["_tile_setup"]
        tile_num = tile_setup["tile_num_list"][file_num]
        base["tile_num"] = tile_num
        nobjects = galsim.config.ParseValue(base["image"], "nobjects", base, int)[0]
        #tile_start_obj_num is the object number of the first object in the current tile
        base["tile_start_obj_num"] = base['start_obj_num'] - tile_setup["file_num_in_tile"][file_num] * nobjects
        
        #Set some eval_variables that can be used in the config file.
        #In particular:
        # - input image filename for wcs
        # - input image psfex filename
        # - tile bounds
        # - magnitude zeropoint (for converting mags to fluxes)
        # - band
        # - probably other stuff
        base["eval_variables"]["sband"] = tile_setup["band_list"][file_num]
        base["eval_variables"]["simage_path"] = tile_setup["image_files"][file_num]
        base["eval_variables"]["fmag_zp"] = tile_setup["mag_zp_list"][file_num]
        base["eval_variables"]["spsfex_path"] = tile_setup["psfex_files"][file_num]
        base["eval_variables"]["fra_min_deg"] = tile_setup["ra_ranges_deg"][tile_num][0]
        base["eval_variables"]["fra_max_deg"] = tile_setup["ra_ranges_deg"][tile_num][1]
        base["eval_variables"]["fdec_min_deg"] = tile_setup["dec_ranges_deg"][tile_num][0]
        base["eval_variables"]["fdec_max_deg"] = tile_setup["dec_ranges_deg"][tile_num][1]

        logger.debug('file_num, ntiles, nband = %d, %d, %d', file_num, ntiles, len(bands))
        logger.debug('tile_num, band = %d, %s', tile_num, base["eval_variables"]["sband"] )
        #print(base["eval_variables"])

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
        
        This function gets called early, before the setup function, as the number of 
        files is required to split up jobs sensibly. So we need to do read in some
        information about the tiles being simulated here
        """
        tilenames = config["tilenames"]
        bands = config["bands"]
        nfiles = 0
        for tilename in tilenames:
            #Read in source lists
            for band in bands:
                source_list = os.path.join( os.environ["DESDATA"], tilename, "lists", "%s_%s_fcut-flist-y3v02.dat"%(tilename, band) )
                with open(source_list, 'r') as f:
                    lines = f.readlines()
                    image_files = [l.strip() for l in lines if l.strip()!=""]
                    nfiles += len(image_files)

        return nfiles

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
        logger.info('tile_num: %d'%base['tile_num'])
        logger.info('file_num: %d'%base['file_num'])
        logger.info('image_num: %d'%base['image_num'])

        ignore += ["tilenames", "bands"]
        ignore += [ 'file_name', 'dir' ]

        images = OutputBuilder.buildImages(self, config, base, file_num, image_num, obj_num,
                                           ignore, logger)
        return images
    


galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('DESTile', DESTileBuilder())

