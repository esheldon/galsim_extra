# This file defines a few types that are used in conjunction with each other.
#
# The basic idea is that if you are following real data files as inputs, you may not always
# have the same number of CCDs for each exposure.  Some may have been excluded or be off the edge
# of a coadd region, etc.  So this module lets you automatically use just the Files that are
# present in the directory.
#
# * all_files is an input type that finds all the files of a certain form (`files`) in some
#   directory and extracts from that a list of file ids that replace the '*' in the files string.
# * NFiles is an integer value type that returns the number of files matched by the glob string.
# * ThisFileName is the full file name in that directory
# * ThisFileTag is a string value type that returns just the part that replaced the '*' in the
#   glob string.

from __future__ import absolute_import
import glob
import os
import galsim

class AllFiles(object):
    """A class for reading in all the file names in a directory that match a given glob string.

    It is connected to the following other value types:

    NFiles          An integer value giving the number of files matched.
    ThisFileName    The current file name from this listing.  (Uses either the current index
                    or can set index_key if desired.)
    ThisFileTag     The part of the current file name that replaced the '*' in the original
                    glob tag.  Often this will be a CCD identifier or something similar.

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
        glob_symbol="*"
        if '*' not in files:
            if "?" not in files:
                raise ValueError("The files string must have a single * or a contiguous series of ? characters.")
            else:
                asterisk=False
                #get indices of ?, and make sure they are consecutive
                inds = [i for (i,c) in enumerate(files) if c=="?"] #this gets the indices
                glob_symbol="?"*len(inds)
                if glob_symbol not in files: #this checks they're contiguous
                    raise ValueError("Only a contiguous series of ? characters is allowed")

        if ('*' in dir) or ('?' in dir):
            raise ValueError("The * or ? characters may not be in dir")
        if files.count('*') > 1:
            raise ValueError("Only a single * character is allowed in files")

        full_path = os.path.join(dir, files)
        self.file_names = sorted(glob.glob(full_path))

        if len(self.file_names) == 0:
            msg = "No files matching %s found"%files
            if dir: msg += " in directory %s"%dir
            raise IOError(msg)

        prefix, sep_, postfix = full_path.partition(glob_symbol)
        i1 = len(prefix)
        i2 = -len(postfix)
        if i2 == 0: i2 = None   # In case no postfix, -0 won't work.  But None does.
        self.tags = [ fname[i1:i2] for fname in self.file_names ]

    def get_nfile(self):
        """Return the number of files.
        """
        return len(self.file_names)

    def get_file_name(self, index):
        """Return the nth file name
        """
        return self.file_names[index]

    def get_tag(self, index):
        """Return the nth tag
        """
        return self.tags[index]


def NFiles(config, base, value_type):
    all_files = galsim.config.GetInputObj('all_files', config, base, 'NFiles')
    return all_files.get_nfile()

def ThisFileName(config, base, value_type):
    all_files = galsim.config.GetInputObj('all_files', config, base, 'ThisFileName')
    index, index_key = galsim.config.GetIndex(config, base)
    return all_files.get_file_name(index)

def ThisFileTag(config, base, value_type):
    all_files = galsim.config.GetInputObj('all_files', config, base, 'ThisFileTag')
    index, index_key = galsim.config.GetIndex(config, base)
    return all_files.get_tag(index)


galsim.config.RegisterInputType('all_files', galsim.config.InputLoader(AllFiles, file_scope=True))
galsim.config.RegisterValueType('NFiles', NFiles, [int], input_type='all_files')
galsim.config.RegisterValueType('ThisFileTag', ThisFileTag, [str], input_type='all_tags')
galsim.config.RegisterValueType('ThisFileName', ThisFileName, [str], input_type='all_files')
