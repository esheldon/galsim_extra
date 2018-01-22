

import galsim
import numpy as np
import os

class MultiGaussianSampler(object):
    """Implements the MultiGaussianValue type. Sample object properties 
    from multiple multivariate Gaussian probability distributions.
    """

    _req_params = { 'amplitudes' : list, 'means' : list, 'covs' : list }
    _opt_params = { 'ranges' : list }

    _single_params = []
    _takes_rng = True # It doesn't actually need an rng, but this marks it as "unsafe"
                      # to the ProcessInput function, which avoids some multiprocessing
                      # pickle problems.

    def __init__(self, amplitudes, means, covs, ranges=None, rng=None):
        """
        @param amplitudes       List of amplitudes of components of length n_component
        @param mean             Length n_component list of length n_dim lists of means of components
        @param covs             Length n_component list of length n_dim*(n_dim+1)lists 
                                of upper triangular elements of covariance of components
        @param ranges           Length n_component list of length n_dim lists of ranges
        """
        self.amps = np.array(amplitudes)
        #normalize amplitudes
        self.amps/=self.amps.sum()
        self.ncomp = len(amplitudes)
        self.nparam = len(means[0])
        self.load_means( means )
        self.load_covs( covs )
        assert len(self.means) == len(self.covs) == self.ncomp

    def load_means( self, means ):
        self.means = []
        for m in means:
            assert len(m) == self.nparam
            self.means.append(np.array(m))

    def load_covs( self, covs ):
        #the covs are provided as a list of upper triangular elements - so need to generate
        #symmetric covariance from this
        self.covs=[]
        for cov_tri_vals in covs:
            assert len(cov_tri_vals) == self.nparam * ( self.nparam + 1 ) / 2 #check there is the correct number of entries
            cov = np.zeros((self.nparam,self.nparam))
            k=0
            #Fill the upper triangle
            for i in range(self.nparam):
                for j in range(i,self.nparam):
                    cov[i,j] = cov_tri_vals[k]
                    k+=1
            #then make symmetric
            cov = cov + cov.T - np.diag(cov.diagonal())
            self.covs.append(cov)

    def sample( self, rng, size=None ):

        if size is None:
            size=1
            is_scalar=True
        else:
            is_scalar=False

        output_sample_data=np.zeros( (size, self.nparam) )

        rand = np.random.RandomState(rng.raw())
        #First choose a component:
        sample_comps = rand.choice( np.arange(self.nparam, dtype=int), replace=True, size=size, p=self.amps )
        #Then loop through the components, sampling from the relevant Gaussian
        for i_comp in range(self.ncomp):
            sample_inds = np.where(sample_comps==i_comp)
            if not is_scalar:
                sample_inds = sample_inds[0]
            samples = rand.multivariate_normal( self.means[i_comp], self.covs[i_comp], size )
            output_sample_data[sample_inds] = samples

        if is_scalar:
            output_sample_data = output_sample_data[0,:]

        return output_sample_data

def MultiGaussianAllProps(config, base, name):
    "Generate a realization of all properties"
    index, index_key = galsim.config.GetIndex(config, base)
    rng = galsim.config.GetRNG(config, base)

    if base.get('_multigaussian_sampler_index',None) != index:
        multigaussian_sampler = galsim.config.GetInputObj('multigaussian_sampler', config, base, name)
        sampled_properties = multigaussian_sampler.sample(rng)
        base['_multigaussian_properties'] = sampled_properties
        base['_multigaussian_sampler_index'] = index
    else:
        sampled_properties = base['_multigaussian_properties']
    return sampled_properties

def MultiGaussianValue(config, base, value_type):
    "Generate specific property"
    sampled_properties = MultiGaussianAllProps(config, base, 'MultiGaussianValue')
    item_num = galsim.config.ParseValue(config, 'item_num', base, int)[0]
    return sampled_properties[item_num]

galsim.config.RegisterInputType('multigaussian_sampler', galsim.config.InputLoader(MultiGaussianSampler))
galsim.config.RegisterValueType('MultiGaussianValue', MultiGaussianValue, [float], input_type='multigaussian_sampler')













