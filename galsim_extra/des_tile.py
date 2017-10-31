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

        print "files:"
        print self.files
        print "exp_nums:"
        print self.exp_nums

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
        self.minra = np.min(ra_list) / galsim.radians
        self.maxra = np.max(ra_list) / galsim.radians
        self.mindec = np.min(dec_list) / galsim.radians
        self.maxdec = np.max(dec_list) / galsim.radians

    def get_nfile(self):
        """Return the number of files.
        """
        return len(self.exp_nums)

    def get_nexp(self):
        return len(self.unique_im_dirs)

    def get_file_name(self, index):
        return self.files[index]

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
    return tile.get_file_name(index)

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
        #if 'exp_num' not in galsim.config.process.valid_index_keys:
        #    galsim.config.process.valid_index_keys += ['exp_num']
        if 'nfiles' in config:
            return galsim.config.ParseValue(config, 'nfiles', base, int)[0]
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
        #n_images is the number of images in the tile, across all the input exposures, of which
        #there are nexp.
        req = { 'nimages' : int, 'nexp' : int}
        ignore += [ 'file_name', 'dir' ]

        kwargs, safe = galsim.config.GetAllParams(config, base, req=req, ignore=ignore)

        nimages, nexp = kwargs['nimages'], kwargs['nexp']

        if 'eval_variables' not in base:
            base['eval_variables'] = {}

        #Generate psf parameters for each exposure from the meta_params.
        #Attempted to do this by generating a list of meta_params for each key.
        #For each exposure, replacing base['meta_params'] with it's original 
        #value means it is evaluated again.
        if 'meta_params' in base:
            meta_param_list_dict = {}  #dict of meta_param lists
            meta_params_orig = copy.deepcopy(base['meta_params'])
            for iexp in range(nexp):
                base['rng'] = galsim.BaseDeviate(1234+iexp)
                for key in base['meta_params']:
                    if key not in meta_param_list_dict:
                        meta_param_list_dict[key]=[]
                    param = galsim.config.ParseValue(base['meta_params'], key, base, float)[0]
                    meta_param_list_dict[key].append(param)
                base['meta_params'] = meta_params_orig

            #Now save to eval variables - the idea is the psf parameters for the current exposure can be
            #recovered from this list using ThisExpNum
            base['eval_variables']['f%s'%(key)] = meta_param_list_dict[key]

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
        simple_config['nfiles'] = nimages
        simple_config['type'] = 'Fits'
        base['output'] = simple_config
        if 'nproc' in base['image']:
            simple_config['nproc'] = base['image']['nproc']
        #base['exp_num'] = base['file_num']
#
        if 'nexp' not in galsim.config.output.output_ignore:
            galsim.config.output.output_ignore += ['nexp', 'nimages']

        galsim.config.BuildFiles(nimages, base, file_num, logger=logger)

        # Go back to the original dict.
        base['output'] = config

        # The calling function is expecting to get some images to write.  Give it something
        # to avoid errors, but we won't write these.
        return [galsim.Image()] * nimages

    
    #def getFilename(self, config, base, logger):
    #    """Get the file_name for the current file being worked on.
#
    #    Note that the base class defines a default extension = '.fits'.
    #    This can be overridden by subclasses by changing the default_ext property.
#
    #    @param config           The configuration dict for the output type.
    #    @param base             The base configuration dict.
    #    @param ignore           A list of parameters that are allowed to be in config['output']
    #                            that we can ignore here.  i.e. it won't be an error if these
    #                            parameters are present.
    #    @param logger           If given, a logger object to log progress.
#
    #    @returns the filename to build.
    #    """
    #    # Typically, the filename will depend on the chip_num, but if this gets called before
    #    # buildImages, then it won't be ready, so just check.
    #    if 'eval_variables' not in base:
    #        base['eval_variables'] = {}
    #    #if 'ichip_num' not in base['eval_variables']:
    #    #    base['eval_variables']['ichip_num'] = 0
    #    #if 'iexp_num' not in base['eval_variables']:
    #    #    base['eval_variables']['iexp_num'] = base['file_num']
    #    #if 'exp_num' not in base:
    #    #    base['exp_num'] = base['file_num']
    #    return super(DESTileBuilder, self).getFilename(config, base, logger)
    

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
        if 'nimages' not in config:
            raise AttributeError("Attribute output.nimages is required for output.type = DesTile")
        return galsim.config.ParseValue(config,'nimages',base,int)[0]

    # Both of these steps will already have been done by the Fits builder.  Don't do anything here.
    def addExtraOutputHDUs(self, config, data, logger):
        return data

    def writeExtraOutputs(self, config, data, logger):
        pass

galsim.config.process.top_level_fields += ['meta_params']
galsim.config.output.RegisterOutputType('DESTile', DESTileBuilder())

