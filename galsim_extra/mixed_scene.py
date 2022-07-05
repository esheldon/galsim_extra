
import galsim
import numpy as np
import coord

class MixedSceneBuilder(galsim.config.StampBuilder):

    def setup(self, config, base, xsize, ysize, ignore, logger):
        if 'objects' not in config:
            raise AttributeError('objets field is required for MixedScene stamp type')
        objects = config['objects']

        # Propagate any stamp rng_num or index_key into the various object fields:
        objects.pop('rng_num', None)  # Also remove them from here if necessary.
        objects.pop('index_key', None)
        if not config.get('_propagated_rng_index', False):
            config['_propagated_rng_index'] = True
            rng_num = config.get('rng_num', None)
            index_key = config.get('index_key', None)
            for key in objects.keys():
                galsim.config.PropagateIndexKeyRNGNum(base[key], index_key, rng_num)

        rng = galsim.config.GetRNG(config, base)
        ud = galsim.UniformDeviate(rng)
        p = ud()  # A random number between 0 and 1.

        # If the user is careful, this will be 1, but if not, renormalize for them.
        norm = float(sum(objects.values()))

        if 'obj_type' in config:
            obj_type = galsim.config.ParseValue(config, 'obj_type', base, str)[0]
            obj_type_index = list(objects.keys()).index(obj_type)
        else:
            # Figure out which object field to use
            obj_type = None  # So we can check that it was set to something.
            obj_type_index = 0
            for key, value in objects.items():
                p1 = value / norm
                if p < p1:
                    # Use this object
                    obj_type = key
                    break
                else:
                    p -= p1
                    obj_type_index += 1
            if obj_type is None:
                # This shouldn't happen, but maybe possible from rounding errors.  Use the last one.
                obj_type = list(objects.keys())[-1]
                obj_type_index -= 1
                logger.error("Error in MixedScene.  Didn't pick an object to use.  Using %s",obj_type)

        # Save this in the dict so it can be used by e.g. the truth catalog or to do something
        # different depending on which kind of object we have.
        base['current_obj_type'] = obj_type
        base['current_obj_type_index'] = obj_type_index
        base['current_obj'] = None

        # Add objects field to the ignore list
        # Also ignore magnify and shear, which we allow here for convenience to act on whichever
        # object ends up being chosen.
        ignore = ignore + ['objects', 'magnify', 'shear', 'obj_type', 'shear_scene']

        stamp_xsize, stamp_ysize, image_pos, world_pos = super(MixedSceneBuilder, self).setup(config,base,xsize,ysize,ignore,logger)
        
        if 'shear_scene' in config:
            shear_scene = galsim.config.ParseValue(config, 'shear_scene', base, bool)[0]
        else:
            shear_scene = False
        
        # option to shear the full scene.
        if shear_scene:       
            shear = galsim.config.ParseValue(config, 'shear', base, float)[0]
            S = shear.getMatrix()
            # Find the center (tangent point) of the scene in RA, DEC. 
            scene_center = base['world_center']
            wcs = base['coadd_wcs']
            if wcs.isCelestial:
                u, v = scene_center.project(world_pos, projection='gnomonic')
                pos = galsim.Position(u.rad, v.rad)
                sheared_pos = pos.shear(shear)
                u2 = sheared_pos.x * coord.radians
                v2 = sheared_pos.y * coord.radians
                world_pos = scene_center.deproject(u2, v2, projection='gnomonic')
            else:
                world_pos = world_pos.shear(shear)
            image_pos = wcs.toImage(world_pos)

        # Now go on and do the rest of the normal setup.
        return stamp_xsize, stamp_ysize, image_pos, world_pos

    def buildProfile(self, config, base, psf, gsparams, logger):
        obj_type = base['current_obj_type']

        # Make the appropriate object using the obj_type field
        obj = galsim.config.BuildGSObject(base, obj_type, gsparams=gsparams, logger=logger)[0]
        # Also save this in case useful for some calculation.
        base['current_obj'] = obj

        # Only shear and magnify are allowed, but this general TransformObject function will
        # work to implement those.
        obj, safe = galsim.config.TransformObject(obj, config, base, logger)

        if psf:
            if obj:
                return galsim.Convolve(obj,psf)
            else:
                return psf
        else:
            if obj:
                return obj
            else:
                return None

galsim.config.stamp.RegisterStampType('MixedScene', MixedSceneBuilder())
