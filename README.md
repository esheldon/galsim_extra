# galsim_extra

A package of modules that can be loaded in galsim config files using the `modules` option.

To use these in a GalSim configuration file you will need to do the following:

1. Download or clone this repo.  e.g.
    ```
    git clone git@github.com:esheldon/galsim_extra.git
    ```

2. Type `python setup.py install` (possibly with `sudo` or `--prefix=~` or similar as you prefer)

3. Add the following somewhere in your configuration file
    ```
    modules:
        - galsim_extra
    ```

4. Use any of the `galsim_extra` module types in your config file.

# Notable modules available in this repo

* `cosmos_sampler` is an input type that reads in the `real_galaxy_25.2_fits.fits` COSMOS
  catalog shipped with GalSim  and calculates the joint PDF for flux and sizes.  Then you can
  sample from that with value types `CosmosR50` and `CosmosFlux` which will produce appropriately
  correlated values for your galaxy population.  cf. examples/focal.yaml

* `FocalPlane` is an output type that lets you have parameters that are randomly generated once
  per focal plane to be used consistently across multiple CCD images.  It adds a top-level field
  called `meta_params`, which generates values that can be used in eval statements elsewhere
  in the config file.  e.g. PSF parameters that set the overall PSF pattern, but which change
  randomly each exposure.

  It also automatically calculates some parameters that may be helpful about the overall focal
  plane geometry.  e.g. `fov_minra`, `fov_maxra`, `pointing_ra`, `pointing_dec`, etc.

  Finally, it adds `exp_num` as an additional `index_key` that you can use to set values to
  only update each new exposure, rather than each file or image.  cf. examples/focal.yaml

* `MixedScene` is a stamp type that lets you have several different kinds of objects in your
  scene with different probabilities.  e.g. stars, bright galaxies, faint galaxies, etc.
  Each object gets its own top-level field, which can be named anything you like, to replace
  the normal single `gal` field.  (You can still have `gal` as one of your fields if you like.)
  cf. examples/focal.yaml

* `OffChip` is a bool value type that checks if an object is (significantly) off the image
  currently being worked on.  Useful in conjunction with the FocalPlane output type.
  cf. examples/focal.yaml

* `LogNormal` is a float value type that samples from a log normal distribution.

* `ExcludedRandom` is an int value type that samples from a given range (min to max), but
  excluding a specified list of integers.  Useful for DES CCD numbers to avoid the bad CCDs.

* `des_wcs` is an input type to enable the `DES_Local` wcs type.  It returns the local Jacobian
  wcs for an arbitrary ccd number and image position from a given DES WCS solution.
  cf. examples/des/meds.yaml in the GalSIm repo.

* 'WrongWCS' is an image type that is identical to the normal Scattered image type, except that it
  changes the wcs to something different (`output_wcs`) before writing the image to disk.  This
  is useful for characterizing the impact of wcs errors on subsequent measurements.
  cf. examples/wrongwcs.yaml.

* `all_files` is an input type that gets the names of all the files in a directory matching a
  particular glob string.  This is useful when the number of CCDs say for your various exposures
  is not constant.  e.g. Some files may be excluded for not being part of a coadd set or might
  not have been written due to some kind of error upstream.  This type lets you dynamically use
  only the files that are present in the directory.  It is connected to value types NFiles,
  ThisFileName and ThisFileTag.

* More.  This is not an exhaustive listing.  There are other modules that were made for targeted
  investigations, which are not likely to be of wider interest.  Although, of course feel free to
  peruse the files and use anything that seems like it might be helpful.
