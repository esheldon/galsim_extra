from galsim.catalog import Catalog
from galsim.config.input import RegisterInputType, RegisterValueType, InputLoader, GetInputObj
from galsim.config.value import SetDefaultIndex, GetAllParams, _GetBoolValue

class FITSCatalog(Catalog):
    """This FITSCatalog inherits from the base GalSim Catalog but supports
    native FITS filtering via fitsio.
    """

    _req_params = { 'file_name' : str }
    _opt_params = { 'dir' : str , 'hdu' : int , 'query' : str }

    def __init__(self, file_name, dir=None, hdu=1, query=None):

        # First build full file_name
        self.file_name = file_name.strip()
        if dir is not None:
            import os
            self.file_name = os.path.join(dir,self.file_name)

        self.file_type = 'FITS'
        self.comments = None
        self.hdu = hdu

        if query == '': query = None
        self.query = query

        if file_type == 'FITS':
            self.readFits()

    def readFits(self):
        import fitsio
        with fitsio.FITS(self.file_name) as fits:
            if self.query is not None:
                w = fits[1].where(self.query)
                self._data = fits[1][w].copy()
            else:
                self._data = fits[1].copy()
        self.names = self._data.dtype.names
        self.nobjects = len(self._data)
        self._ncols = len(self.names)
        self.isfits = True

def _GenerateFromFITSCatalog(config, base, value_type):
    """Return a value read from an input catalog
    """
    input_cat = GetInputObj('fits_catalog', config, base, 'FITSCatalog')

    # Setup the indexing sequence if it hasn't been specified.
    # The normal thing with a Catalog is to just use each object in order,
    # so we don't require the user to specify that by hand.  We can do it for them.
    SetDefaultIndex(config, input_cat.getNObjects())

    # Coding note: the and/or bit is equivalent to a C ternary operator:
    #     input_cat.isFits() ? str : int
    # which of course doesn't exist in python.  This does the same thing (so long as the
    # middle item evaluates to true).
    req = { 'col' : input_cat.isFits() and str or int , 'index' : int }
    opt = { 'num' : int }
    kwargs, safe = GetAllParams(config, base, req=req, opt=opt)
    col = kwargs['col']
    index = kwargs['index']

    if value_type is str:
        val = input_cat.get(index, col)
    elif value_type is float:
        val = input_cat.getFloat(index, col)
    elif value_type is int:
        val = input_cat.getInt(index, col)
    else:  # value_type is bool
        val = _GetBoolValue(input_cat.get(index, col))

    #print(base['file_num'],'Catalog: col = %s, index = %s, val = %s'%(col, index, val))
    return val, safe

RegisterInputType("fits_catalog", InputLoader(FITSCatalog, has_nobj=True))
RegisterValueType('FITSCatalog', _GenerateFromFITSCatalog, [ float, int, bool, str ], input_type='fits_catalog')
