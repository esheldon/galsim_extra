import galsim
import os
import numpy as np
import copy

from galsim.config.output import OutputBuilder

class TileInput(object):
    """A class for for inputting DES tile information.

    It is connected to the following other value types:

    TileNFiles          An integer value giving the number of images in the tile.
    TileNExp            An integer value givin the number of exposures in the tile.
    TileThisFileName    The current image file name from this listing.  (Uses either the current index
                        or can set index_key if desired.)
    ThisExpNum          The current exposure number - an integer index, starting from zero, 
                        recording the current exposure in the tile (not an official DES exposure
                        number)
    ThisChipNum         The current chip number (just [0, number of chips] - not an offical ccd number or anything)
    TileRAMin           Minimum ra, with which to simulate objects - this is inferred from the coadd file.

    @param source_list     The file containing a list of source exposures filenames and zero-points for the tile
    @param coadd_file      Coadd image file - used for it's wcs....
    """
    # The normal way to tell GalSim what parameters are required and/or optional is
    # through some class attributes given here:
    _req_params = {
        "source_list" : str,    # The file containing a list of source exposures for the tile
        "coadd_file" : str
    }
    # And some other attributes that are required to be present if you do the above.
    _opt_params = {}
    _single_params = []
    _takes_rng = False

    def __init__(self, source_list, coadd_file):
        #Read in the text file and produce lists of exposure number (here 
        #this is just and index, rather than some official thing). 
        #filename, and magnitude zeropoint. 
        #Images from the same exposure are identified by being in the same 
        #directory.
        self.exp_nums=[]
        self.files=[]
        self.mag_zps=[]
        self.unique_im_dirs=[]
        with open(source_list,'r') as f:
            lines=f.readlines()
            for l in lines:
                s=(l.strip()).split()
                im_path, mag_zp = os.path.normpath(s[0]), float(s[1])
                im_dir, im_file = os.path.dirname(im_path), os.path.basename(im_path)
                if im_dir not in self.unique_im_dirs:
                    self.unique_im_dirs.append(im_dir)
                exp_num = self.unique_im_dirs.index(im_dir)
                self.exp_nums.append(exp_num)
                self.files.append(im_path)
                self.mag_zps.append(mag_zp)

        #print("files:")
        #print(self.files)
        #print("exp_nums:")
        #print(self.exp_nums)

        #Also read in coadd_file to get bounds
        coadd_header = galsim.FitsHeader(file_name = coadd_file)
        wcs,origin = galsim.wcs.readFromFitsHeader(coadd_header)
        xsize = coadd_header['NAXIS1']
        ysize = coadd_header['NAXIS2']
        im_pos1 = galsim.PositionD(0,0)
        im_pos2 = galsim.PositionD(0,ysize)
        im_pos3 = galsim.PositionD(xsize,0)
        im_pos4 = galsim.PositionD(xsize,ysize)
        corners = []
        corners.append(wcs.toWorld(im_pos1))
        corners.append(wcs.toWorld(im_pos2))
        corners.append(wcs.toWorld(im_pos3))
        corners.append(wcs.toWorld(im_pos4))
        ra_list = [p.ra.wrap(corners[0].ra) for p in corners]
        dec_list = [p.dec for p in corners]
        self.minra = np.min(np.array([ra/galsim.radians for ra in ra_list]))
        self.maxra = np.max(np.array([ra/galsim.radians for ra in ra_list]))
        self.mindec = np.min(np.array([dec/galsim.radians for dec in dec_list]))
        self.maxdec = np.min(np.array([dec/galsim.radians for dec in dec_list]))

    def get_nfile(self):
        """Return the number of files.
        """
        return len(self.exp_nums)

    def get_nexp(self):
        return len(self.unique_im_dirs)

    def get_filename(self, index):
        return self.files[index]

    def get_psfex_filename(self, index):
        image_filename = self.files[index]
        image_dir = os.path.dirname(image_filename)
        image_base = os.path.basename(image_filename)
        psfex_dir = image_dir.replace("red/immask","psf")
        psfex_base = image_base.replace("immasked.fits.fz", "psfexcat.psf")
        return os.path.join(psfex_dir, psfex_base)

    def get_exp_num(self, index):
        return self.exp_nums[index]

    def get_mag_zp(self, index):
        return self.mag_zps[index]

    def get_min_ra(self):
        return self.minra

    def get_max_ra(self):
        return self.maxra

    def get_min_dec(self):
        return self.mindec

    def get_max_dec(self):
        return self.maxdec

def TileNFiles(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileNFiles')
    return tile.get_nfile()

def TileNExp(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileNExp')
    return tile.get_nexp()
def TileThisFileName(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileThisFileName')
    index, index_key = galsim.config.GetIndex(config, base)
    return tile.get_filename(index)

def TileThisPSFExFileName(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileThisFileName')
    index, index_key = galsim.config.GetIndex(config, base)
    return tile.get_psfex_filename(index)

def ThisExpNum(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'ThisExpNum')
    index, index_key = galsim.config.GetIndex(config, base)
    return tile.get_exp_num(index)

def TileRAMin(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileRAMin')
    return tile.get_min_ra()

def TileRAMax(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileRAMax')
    return tile.get_max_ra()

def TileDecMin(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileDecMin')
    return tile.get_min_dec()

def TileDecMax(config, base, value_type):
    tile = galsim.config.GetInputObj('tile', config, base, 'TileDecMax')
    return tile.get_max_dec()

galsim.config.RegisterInputType('tile', galsim.config.InputLoader(TileInput, file_scope=True))
galsim.config.RegisterValueType('TileNFiles', TileNFiles, [int], input_type='tile')
galsim.config.RegisterValueType('ThisExpNum', ThisExpNum, [int], input_type='tile')
galsim.config.RegisterValueType('TileNExp', TileNExp, [int], input_type='tile')
galsim.config.RegisterValueType('TileThisFileName', TileThisFileName, [str], input_type='tile')
galsim.config.RegisterValueType('TileThisPSFExFileName', TileThisPSFExFileName, [str], input_type='tile')
galsim.config.RegisterValueType('TileRAMin', TileRAMin, [float], input_type='tile')
galsim.config.RegisterValueType('TileRAMax', TileRAMax, [float], input_type='tile')
galsim.config.RegisterValueType('TileDecMin', TileDecMin, [float], input_type='tile')
galsim.config.RegisterValueType('TileDecMax', TileDecMax, [float], input_type='tile')

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
        bands = config["bands"]
        nbands = len(config["bands"])

        #We need to get the tile_num and tile_start_obj_num from file_num
        #This is tricky because different tiles can have different numbers of files,
        #so we can't just say tile_num = file_num // n_files_per_tile
        #So instead, generate a list of tile_num for each file_num:
        if "_tile_num_for_file_num" not in base:
            tile_num_for_file_num = []
            nfiles = 0
            for tile_num in range(ntiles):
                base["tile_num"] = tile_num
                n_images_in_tile = galsim.config.ParseValue(base["input"], "TileNFiles", base, int)[0]
                tile_num_for_file_num += [tile_num] * n_images_in_tile
                nfiles += n_image_in_tile
            base["nfiles"] = nfiles
            base["_tile_num_for_file_num"] = tile_num_for_file_num
            #Also useful is the number of times each list has occured so far - this is the image number within a tile
            #which we'll use below
            l = tile_num_for_file_num
            base["_image_num_in_tile"] = [ l[:i].count(l[i]) for i in range(len(l)) ]
            print("tile_num_for_file_num:", base["_tile_num_for_file_num"])
            print("image_num_in_tile:", base["_tile_num_for_file_num"])
            
        #Now set the tile_num
        base["tile_num"] = base["_tile_num_for_file_num"][file_num]
        #And tile_star_obj_num
        nobjects = galsim.config.ParseValue(base['image'], 'nobjects', base, int)[0]
        #tile_start_obj_num is the object number of the first object in the current tile
        base["tile_start_obj_num"] = base['start_obj_num'] - base["_image_num_in_tile"][file_num] * nobjects

        logger.debug('file_num, ntiles, nband = %d, %d, %d', file_num, ntiles, nbands)
        logger.debug('tile_num, band_num = %d, %d', tile_num, band_num)

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
        if "tile" in base["input"]:
            with open(base["input"]["tile"]["source_list"], "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()!=""]
            nfiles = len(lines)
        else:
            print("Assuming tile input to get ntiles, but couldn't find tile input section")
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

        ignore += ["ntiles", "n_images_in_tile"]
        ignore += [ 'file_name', 'dir' ]

        images = OutputBuilder.buildImages(self, config, base, file_num, image_num, obj_num,
                                           ignore, logger)
        return images
    


galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('DESTile', DESTileBuilder())

