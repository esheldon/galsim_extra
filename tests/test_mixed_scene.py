
import galsim
import numpy as np
import coord
# from ..galsim_extra import MixedSceneBuilder

BASE_CONFIG = {'modules': ["galsim_extra"], 

'input' : { 'cosmos_sampler' : {'min_r50' : 0.15, 'max_r50' : 1., 'min_flux' : 2.5, 'max_flux' : 100 }}, 

'image' : { 'pixel_scale' : 0.26, 'size' : 48, 'random_seed' : 1234, 'nobjects': 1, 'ra': "16:01:41.01257 hours", 
            'dec': "66:48:10.1312 degrees"},

'psf': {'type': 'Gaussian', 'fwhm': 0.9, 'flux': 1.0}, 

#No knots
'gal': {'type': 'Exponential', 'half_light_radius': 0.5, 
    'ellip':{'type': 'G1G2', 'g1': 0.0, 'g2': 0.0}, 
    'flux': {'type': 'Eval', 'str': "10**(0.4*(mag_zp-mag))", 'fmag': 17.}}, 

'stamp': {
    'type': 'MixedScene', 
    'objects': {'star': 0.0, 'gal': 1.0}, 
    'obj_type': 'gal', 
    'draw_method': 'auto', 
    'shear': {'type': 'G1G2', 'g1': 0.02, 'g2': 0.00}, 
    'gsparams': {'maximum_fft_size': 16384}}, 

'output': {
    'dir': 'output', 
    'file_name': "mixed_scene_test.fits"}
}

def test_mixed_scene():

    # Step 1. Run the above config 
    config = galsim.config.CopyConfig(BASE_CONFIG)
    galsim.config.Process(config)

    """
    # MixedSceneBuilder class object
    mixedscenebuilder = mixed_scene.MixedSceneBuilder(...)
    stamp_xsize, stamp_ysize, image_pos, world_pos = mixedscenebuilder.setup(...)

    # Shear scene by hand
    how do i test this function? 
    am i going to test this without using galsim? 

    assert stamp_xsize == xxx
    assert stamp_ysize == yyy
    assert image_pos == zzz
    assert world_pos == aaa
    """

if __name__ == '__main__':
    test_mixed_scene()