import logging

from galsim.config.util import LoggerWrapper
from galsim.config.value import GetAllParams
from galsim.errors import GalSimConfigError
from galsim.sed import SED

from galsim.config.sed import SEDBuilder, RegisterSEDType


class TophatSEDBuilder(SEDBuilder):
    """A class for defining an SED from a set of tophats

    TophatSED expects the following parameters:

        bins (required)         The tophat bins
        values (required)       The tophat values
        wave_type(required)     The units (nm or Ang) of the wavelengths expected by the string function
        flux_type (required)    Which kind of flux values are in the string function
                                Allowed values: flambda, fnu, fphotons, 1
    """
    def buildSED(self, config, base, logger):
        """Build the SED based on the specifications in the config dict.

        Parameters:
            config:     The configuration dict for the SED type.
            base:       The base configuration dict.
            logger:     If provided, a logger for logging debug statements.

        Returns:
            the constructed SED object.
        """
        import numpy as np
        from galsim.config.bandpass import BuildBandpass
        from galsim import LookupTable
        logger = LoggerWrapper(logger)

        req = {'bins': list, 'values': list, 'wave_type': str, 'flux_type': str}
        opt = {'norm_flux_density': float, 'norm_wavelength': float,
               'norm_flux': float, 'redshift': float}
        ignore = ['norm_bandpass']

        kwargs, safe = GetAllParams(config, base, req=req, opt=opt, ignore=ignore)

        bins = kwargs.pop('bins')
        values = kwargs.pop('values')

        if len(bins) != len(values):
            raise GalSimConfigError(
                "SED Tophat bins and values must be of equal size")

        norm_flux_density = kwargs.pop('norm_flux_density', None)
        norm_wavelength = kwargs.pop('norm_wavelength', None)
        norm_flux = kwargs.pop('norm_flux', None)
        redshift = kwargs.pop('redshift', 0.)
        wave_type = kwargs.pop('wave_type')
        flux_type = kwargs.pop('flux_type')

        bins_array = np.asarray(bins).ravel()
        values_array = np.repeat(values, 2)
        tophat_lookuptable = LookupTable(
            x=bins_array,
            f=values_array,
            interpolant='linear',
        )  # Linearly interpolate between the provided tophats
        logger.info("Using SED tophat LookupTable: %s", tophat_lookuptable)
        sed = SED(tophat_lookuptable, wave_type, flux_type)
        if norm_flux_density:
            sed = sed.withFluxDensity(norm_flux_density, wavelength=norm_wavelength)
        elif norm_flux:
            bandpass, safe1 = BuildBandpass(config, 'norm_bandpass', base, logger)
            sed = sed.withFlux(norm_flux, bandpass=bandpass)
            safe = safe and safe1
        sed = sed.atRedshift(redshift)

        return sed, safe

RegisterSEDType('Tophat', TophatSEDBuilder())
