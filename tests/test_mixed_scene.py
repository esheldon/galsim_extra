
import galsim
import galsim_extra
import numpy as np
import coord
import yaml
# from ..galsim_extra import MixedSceneBuilder

BASE_CONFIG = """
modules:
    - galsim_extra

eval_variables :

    # pixel_scale = the pixel scale in arcsec.  Used in setting up the WCS.
    # The units for this doesn't have to be arcsec.  It is set by the wcs.units parameter.
    # Remember the first letter indicates what type each variable is.  Here f = float.
    fpixel_scale : &pixel_scale 0.26

    # image_size = size in pixels
    fimage_size : &image_size 64

    # For simple evaluations, this often makes the config file more readable.
    # This is a calculation of the size of the image in degrees, which we'll use below.
    # size in degrees = 2048 pixels * 0.2 arcsec/pixel / 3600 arcsec/deg = 0.114 deg
    fsize_degrees : '$image_size * pixel_scale / 3600'

gal :
    # Exponential requires one of scale_radius, fwhm, or half_light_radius.
    type : Exponential
    half_light_radius : 0.5  # arcsec
    flux : 1.e4         # counts

psf :
    type : Gaussian
    fwhm : 0.9  # arcsec

star:

    type: DeltaFunction

image :
    size : 64

    # WCS centered around (ra=90,dec=-10) coordinates. 
    wcs: 
        type: 'Tan'
        dudx: 0.26
        dudy: 0.00
        dvdx: 0.00
        dvdy: 0.26
        ra: 90.0 degrees
        dec: -10.0 degrees
        units: 'arcsec'
    random_seed: 12345

    # Make an object at this location on the sky. 
    world_pos:
        type: RADec
        ra:
            # Note: in this case we can't use the $ notation, because we want to define a new
            # variable to use within the eval string.  But if we were able to use the $ notation,
            # it would still be allowed to use @ value in the string as we do here.
            type: Eval
            # Range of RA = RA_center +- image_size / cos(Dec)
            str: "@image.wcs.ra + dtheta / numpy.cos(@image.world_pos.dec) * galsim.degrees"
            fdtheta: { type: Random, min: '$-size_degrees/2.', max: '$size_degrees/2.' }
        dec:
            type: Eval
            # Range of Dec = Dec_center +- image_size
            str: "@image.wcs.dec + dtheta * galsim.degrees"
            fdtheta: { type: Random, min: '$-size_degrees/2.', max: '$size_degrees/2.' }

stamp:
    type: MixedScene
    objects: 
        star: 0
        gal: 1
    draw_method: 'auto'
    shear: 
        type: G1G2
        g1: 0.50
        g2: 0.00
    gsparams:
        maximum_fft_size: 16384

output :
    dir : imsim_output
    file_name : demo14_after.fits
"""

def shear_positions(g1, g2, wcs, radec, world_center ):
    # Shear the positions
    shear = galsim.Shear(g1=g1, g2=g2)
    S = shear.getMatrix()

    u,v = world_center.project_rad(radec.ra, radec.dec, projection='gnomonic') # tile center units in radians
    # shearing the position. 
    pos = np.vstack((u, v))
    sheared_uv = np.dot(S, pos)
    # convert sheared u,v back to sheared ra,dec
    sheared_ra, sheared_dec = world_center.deproject_rad(sheared_uv[0,:].astype(float), sheared_uv[1,:].astype(float), projection='gnomonic')
    # Convert ra, dec to image coordinates
    xy_new = [wcs.toImage(galsim.CelestialCoord(ra*galsim.radians, dec*galsim.radians)) for ra, dec in zip(sheared_ra, sheared_dec)]
    x_new = [coord.x for coord in xy_new]
    y_new = [coord.y for coord in xy_new]
    
    return x_new, y_new

def test_mixed_scene():

    # Step 1. Run the above config to make one stamp that has one object. 
    yml_conf = yaml.safe_load(BASE_CONFIG)
    config1 = galsim.config.CopyConfig(yml_conf) # BASE_CONFIG is 'shear_scene': False
    res_before = galsim.config.Process(config1)

    # Compare to identical run except shear scene for galaxies.
    config2 = galsim.config.CopyConfig(yml_conf)
    config2['stamp']['shear_scene'] = "$@current_obj_type == 'gal'"
    res_after = galsim.config.Process(config2)

    # Step 2. From the WCS of the stamp, RA/DEC of the object, shear the center of the object.
    world_pos = res_before['world_pos']
    targ_pos = galsim.CelestialCoord(ra=90*galsim.degrees, dec=-10*galsim.degrees)
    aff = galsim.AffineTransform(0.26, 0.00, 0.00, 0.26)
    wcs = galsim.TanWCS(aff, targ_pos)

    world_center = res_before['world_center']
    x_new, y_new = shear_positions(0.50, 0.00, wcs, world_pos, world_center)

    # Step 3. Compare the result of step 1 and step 2. 
    image_pos = wcs.toImage(res_after['world_pos'])
    assert image_pos.x == x_new[0]
    assert image_pos.y == y_new[0]

    # Another test: Measure shapes on the unsheared positions for CONFIG1 and on the sheared positions for CONFIG2
    from math import isclose
    image = res_after['current_stamp']
    moms = galsim.hsm.FindAdaptiveMom(image)

    assert isclose(0.50, moms.observed_shape.e1, abs_tol=1e-2)
    assert isclose(0.00, moms.observed_shape.e2, abs_tol=1e-2)
    assert isclose(image_pos.x, moms.moments_centroid.x, abs_tol=1e-5)
    assert isclose(image_pos.y, moms.moments_centroid.y, abs_tol=1e-5)

CONFIG_FLAT = """
modules:
  - galsim_extra

stamp:
  type: MixedScene

  objects:
    star: 0
    gal: 1

  # for ring simulations, we apply the shear in the stamp
  shear:
    type: G1G2
    g1: 0.2
    g2: 0.4

psf:
  type: Gaussian

  fwhm: 0.7

star:
  type: DeltaFunction

gal:
  type: Exponential
  half_light_radius: 0.5
  flux: 1000
  shift:
    type: RandomCircle
    radius: 0.1  # arcsec

image:
  type: Scattered
  nobjects: 1
  xsize: 320
  ysize: 320
  pixel_scale: 0.2  # arcsec / pixel

  random_seed : 42

  image_pos: "$galsim.PositionD(195, 117)"
"""

def test_mixed_scene_flat():
    # Make sure this works for flat sky sims as well.

    yml_conf = yaml.safe_load(CONFIG_FLAT)
    config1 = galsim.config.CopyConfig(yml_conf) # BASE_CONFIG is 'shear_scene': True
    im1 = galsim.config.BuildImage(config1)

    # Compare to identical run except shear scene for galaxies.
    config2 = galsim.config.CopyConfig(yml_conf)
    config2['stamp']['shear_scene'] = "$@current_obj_type == 'gal'"
    im2 = galsim.config.BuildImage(config2)

    # Step 2. This time, the WCS is just a pixel scale
    pixel_scale = config1['image']['pixel_scale']
    image_pos = galsim.PositionD(195, 117)
    world_pos = galsim.PixelScale(pixel_scale).toWorld(image_pos)

    nominal_delta_pos = image_pos - im1.true_center
    sheared_delta_pos = nominal_delta_pos.shear(galsim.Shear(g1=0.2, g2=0.4))
    sheared_pos = im1.true_center + sheared_delta_pos
    print('image_pos = ',image_pos)
    print('sheared_pos = ',sheared_pos)

    b1 = galsim.BoundsI(image_pos).withBorder(15)
    b2 = galsim.BoundsI(sheared_pos.round()).withBorder(15)

    mom1 = galsim.hsm.FindAdaptiveMom(im1[b1])
    mom2 = galsim.hsm.FindAdaptiveMom(im2[b2])

    # Expectation: shape and size are the same, but centroids are different.
    # Note: since there is a PSF, the moment shapes don't match (0.2,0.4) shear value.
    # But they do match each other.

    assert np.isclose(mom1.observed_shape.e1, mom2.observed_shape.e1, atol=1.e-3)
    assert np.isclose(mom1.observed_shape.e2, mom2.observed_shape.e2, atol=1.e-3)
    assert np.isclose(mom1.moments_sigma, mom2.moments_sigma, rtol=1.e-3)
    assert np.isclose(mom1.moments_amp, mom2.moments_amp, rtol=1.e-3)

    assert np.isclose(image_pos.x, mom1.moments_centroid.x, atol=0.2)
    assert np.isclose(image_pos.y, mom1.moments_centroid.y, atol=0.2)
    assert np.isclose(sheared_pos.x, mom2.moments_centroid.x, atol=0.2)
    assert np.isclose(sheared_pos.y, mom2.moments_centroid.y, atol=0.2)


if __name__ == '__main__':
    test_mixed_scene()
    test_mixed_scene_flat()
