# This file defines a few types that are used in conjunction with each other.
#
# The basic idea is that if you are following real data files as inputs, you may not always
# have the same number of CCDs for each exposure.  Some may have been excluded or be off the edge
# of a coadd region, etc.  So this module lets you automatically use just the CCDs that are
# present in the directory.
#
# * all_ccds is an input type that finds all the files of a certain form (`files`) in some
#   directory and extracts from that a list of CCD ids that replace the '*' in the files string.
# * NCCD is an integer value type that returns the number of CCDs in the current exposure
# * CCDName is a string value type that returns the id for the current chip num.
# * CCDFile is the file name in that directory

import glob
import os
import galsim

class AllCCDs(object):
    """A class for reading in a list of file names corresponding to a single exposure and
    finding how many CCDs there are and what their ids are.

    @param dir          The directory with the image files
    @param files        The glob string to use for listing the files.
    """
    # The normal way to tell GalSim what parameters are required and/or optional is
    # through some class attributes given here:
    _req_params = {
        "dir" : str,    # The directory with the files.
        "files" : str,  # The glob string for listing the files.
    }
    # And some other attributes that are required to be present if you do the above.
    _opt_params = {}
    _single_params = []
    _takes_rng = False

    def __init__(self, dir, files):

        if '*' not in files:
            raise ValueError("The character * should be in files where the ccdid goes")
        if '*' in dir:
            raise ValueError("The character * may not be in dir")
        if files.count('*') != 1:
            raise ValueError("Only a single * character is allowed in files")

        full_path = os.path.join(dir, files)
        self.file_names = sorted(glob.glob(full_path))

        if len(self.file_names) == 0:
            msg = "No files matching %s found"%files
            if dir: msg += " in directory %s"%dir
            raise IOError(msg)

        prefix, sep_, postfix = full_path.partition('*')
        i1 = len(prefix)
        i2 = -len(postfix)
        if i2 == 0: i2 = None   # In case no postfix, -0 won't work.  But None does.
        self.ccd_names = [ fname[i1:i2] for fname in self.file_names ]

    def get_nccd(self):
        """Return the number of ccds.
        """
        return len(self.ccd_names)

    def get_ccd_name(self, index):
        """Return the nth ccd name
        """
        return self.ccd_names[index]

    def get_file_name(self, index):
        """Return the nth file name
        """
        return self.file_names[index]


def NCCD(config, base, value_type):
    all_ccds = galsim.config.GetInputObj('all_ccds', config, base, 'NCCD')
    return all_ccds.get_nccd()

def CCDName(config, base, value_type):
    all_ccds = galsim.config.GetInputObj('all_ccds', config, base, 'CCDName')
    index, index_key = galsim.config.GetIndex(config, base)
    return all_ccds.get_ccd_name(index)

def CCDFile(config, base, value_type):
    all_ccds = galsim.config.GetInputObj('all_ccds', config, base, 'CCDFile')
    index, index_key = galsim.config.GetIndex(config, base)
    return all_ccds.get_file_name(index)


galsim.config.RegisterInputType('all_ccds', galsim.config.InputLoader(AllCCDs, file_scope=True))
galsim.config.RegisterValueType('NCCD', NCCD, [int], input_type='all_ccds')
galsim.config.RegisterValueType('CCDName', CCDName, [str], input_type='all_ccds')
galsim.config.RegisterValueType('CCDFile', CCDFile, [str], input_type='all_ccds')
