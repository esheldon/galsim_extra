import galsim
import numpy
import os

class CosmosSampler(object):
    _req_params = {}
    _opt_params = { 'min_r50' : float, 'max_r50': float,
                   'min_flux' : float, 'max_flux': float,
                   'kde_factor' : float }
    _single_params = []
    _takes_rng = False

    def __init__(self, min_r50=0.05, max_r50=2.0, min_flux=0.5, max_flux=100,
                 kde_factor=0.01):
        # Make sure required dependencies are checked right away, so the user gets timely
        # feedback of what this code requires.
        import scipy
        import fitsio
        self.r50_range = (min_r50, max_r50)
        self.flux_range = (min_flux, max_flux)

        self.r50_sanity_range=0.05,2.0
        self.flux_sanity_range=0.5,100.0
        self.kde_factor=kde_factor

        self._load_data()
        self._make_kde()

    def sample(self, rng, size=None):
        """
        get [r50, flux] or [:, r50_flux]
        """
        if size is None:
            size=1
            is_scalar=True
        else:
            is_scalar=False

        r50min,r50max=self.r50_range
        fmin,fmax=self.flux_range

        data=numpy.zeros( (size,2) )

        ngood=0
        nleft=data.shape[0]
        numpy.random.seed(rng.raw())
        while nleft > 0:
            r=self.kde.resample(size=nleft).T

            w,=numpy.where( (r[:,0] > r50min) &
                            (r[:,0] < r50max) &
                            (r[:,1] > fmin) &
                            (r[:,1] < fmax)
            )

            if w.size > 0:
                data[ngood:ngood+w.size,:] = r[w,:]
                ngood += w.size
                nleft -= w.size

        if is_scalar:
            data=data[0,:]

        return data

    def _load_data(self):
        import fitsio
        fname='real_galaxy_catalog_25.2_fits.fits'
        fname=os.path.join(
            #sys.exec_prefix,
            #'share',
            #'galsim',
            galsim.meta_data.share_dir,
            'COSMOS_25.2_training_sample',
            fname,
        )

        r50min,r50max=self.r50_sanity_range
        fmin,fmax=self.flux_sanity_range

        alldata=fitsio.read(fname, lower=True)
        w,=numpy.where(
            (alldata['viable_sersic']==1) &
            (alldata['hlr'][:,0] > r50min) &
            (alldata['hlr'][:,0] < r50max) &
            (alldata['flux'][:,0] > fmin) &
            (alldata['flux'][:,0] < fmax)
        )

        self.alldata=alldata[w]

    def _make_kde(self):
        import scipy.stats

        data=numpy.zeros( (self.alldata.size, 2) )
        data[:,0] = self.alldata['hlr'][:,0]
        data[:,1] = self.alldata['flux'][:,0]

        self.kde=scipy.stats.gaussian_kde(
            data.transpose(),
            bw_method=self.kde_factor,
        )

def CosmosR50Flux(config, base, name):

    index, index_key = galsim.config.GetIndex(config, base)
    rng = galsim.config.GetRNG(config, base)

    if base.get('_cosmos_sampler_index',None) != index:
        cosmos_sampler = galsim.config.GetInputObj('cosmos_sampler', config, base, name)
        r50, flux = cosmos_sampler.sample(rng)
        base['_cosmos_sampler_r50'] = r50
        base['_cosmos_sampler_flux'] = flux
        base['_cosmos_sampler_index'] = index
    else:
        r50 = base['_cosmos_sampler_r50']
        flux = base['_cosmos_sampler_flux']

    return float(r50), float(flux)


def CosmosR50(config, base, value_type):
    r50, flux = CosmosR50Flux(config,base,'CosmosR50')
    return r50, False

def CosmosFlux(config, base, value_type):
    r50, flux = CosmosR50Flux(config,base,'CosmosFlux')
    return flux, False

galsim.config.RegisterInputType('cosmos_sampler', galsim.config.InputLoader(CosmosSampler))
galsim.config.RegisterValueType('CosmosR50', CosmosR50, [float], input_type='cosmos_sampler')
galsim.config.RegisterValueType('CosmosFlux', CosmosFlux, [float], input_type='cosmos_sampler')


