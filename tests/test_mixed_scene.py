
import galsim
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
    scale_radius : 2.7  # arcsec
    flux : 1.e6         # counts

psf :
    type : Moffat
    beta : 2.9
    half_light_radius : 0.7  # arcsec

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
    shear_scene: False
    shear: 
        type: G1G2
        g1: 0.02
        g2: 0.00
    gsparams:
        maximum_fft_size: 16384

output :
    dir : imsim_output
    file_name : demo14_after.fits
"""

CONFIG_2 = """
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
    scale_radius : 2.7  # arcsec
    flux : 1.e6         # counts

psf :
    type : Moffat
    beta : 2.9
    half_light_radius : 0.7  # arcsec

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
    shear_scene: True
    shear: 
        type: G1G2
        g1: 0.02
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
    # config1 = galsim.config.ReadConfig('/Users/masayayamamoto/Desktop/DarkEnergySurvey/demo14.yaml')
    res_before = galsim.config.Process(config1)

    yml_conf = yaml.safe_load(CONFIG_2)
    config2 = galsim.config.CopyConfig(yml_conf) # BASE_CONFIG is 'shear_scene': True
    # config2 = galsim.config.ReadConfig('/Users/masayayamamoto/Desktop/DarkEnergySurvey/demo14_1.yaml')
    res_after = galsim.config.Process(config2)

    # Step 2. From the WCS of the stamp, RA/DEC of the object, shear the center of the object.
    world_pos = res_before['world_pos']
    targ_pos = galsim.CelestialCoord(ra=90*galsim.degrees, dec=-10*galsim.degrees)
    aff = galsim.AffineTransform(0.26, 0.00, 0.00, 0.26)
    wcs = galsim.TanWCS(aff, targ_pos)

    world_center = res_before['world_center']
    x_new, y_new = shear_positions(0.02, 0.00, wcs, world_pos, world_center)

    # Step 3. Compare the result of step 1 and step 2. 
    image_pos = wcs.toImage(res_after['world_pos'])

    assert image_pos.x == x_new[0]
    assert image_pos.y == y_new[0]


if __name__ == '__main__':
    test_mixed_scene()