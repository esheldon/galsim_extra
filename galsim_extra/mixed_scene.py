
import galsim

class MixedSceneBuilder(galsim.config.StampBuilder):

    def setup(self, config, base, xsize, ysize, ignore, logger):
        # Build all the kinds of objects once to make sure there is something as the
        # current_val for everything.  Simplifies the ability to get current values of
        # things in a truth catalog.
        objects = config['objects']
        for key in objects:
            galsim.config.BuildGSObject(base, key)

        # Now go on and do the rest of the normal setup.
        ignore = ignore + ['objects']
        return super(self.__class__,self).setup(config,base,xsize,ysize,ignore,logger)

    def buildProfile(self, config, base, psf, gsparams, logger):
        objects = config['objects']
        rng = galsim.config.GetRNG(config, base)
        ud = galsim.UniformDeviate(rng)
        p = ud()  # A random number between 0 and 1.

        # If the user is careful, this will be 1, but if not, renormalize for them.
        norm = float(sum(objects.values()))

        # Figure out which object field to use
        obj_type = None  # So we can check that it was set to something.
        for key, value in objects.items():
            p1 = value / norm
            if p < p1:
                # Use this object
                obj_type = key
                break
            else:
                p -= p1
        if obj_type is None:
            # This shouldn't happen, but maybe possible from rounding errors.  Use the last one.
            obj_type = objects.items()[-1][1]
            logger.error("Error in MixedScene.  Didn't pick an object to use.  Using %s",obj_type)
        # Save this in the dict so it can be used by e.g. the truth catalog or to do something
        # different depending on which kind of object we have.
        base['current_obj_type'] = obj_type

        # Make the appropriate object using the obj_type field
        obj = galsim.config.BuildGSObject(base, obj_type, gsparams=gsparams, logger=logger)[0]
        # Also save this in case useful for some calculation.
        base['current_obj'] = obj
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
