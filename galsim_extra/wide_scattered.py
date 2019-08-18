#
# This module is a very simple modification of the normal Scattered image type.
# After building the image the normal way, just before it writes out the image to disk,
# it slaps on a different wcs.

import galsim
import coord
import numpy as np

class WideScatteredBuilder(galsim.config.image_scattered.ScatteredImageBuilder):

    def setup(self, config, base, image_num, obj_num, ignore, logger):
        ignore = ignore + ['border']
        return super(WideScatteredBuilder, self).setup(config, base, image_num, obj_num, ignore, logger)

    def buildImage(self, config, base, image_num, obj_num, logger):
        # Copy the Scattered buildImage function, but with changes to skip building stamps that
        # are clearly not in the image.

        #print('start buildImage')
        xsize = base['image_xsize']
        ysize = base['image_ysize']
        wcs = base['wcs']

        image = galsim.ImageF(xsize, ysize)
        image.setOrigin(base['image_origin'])
        image.wcs = wcs
        image.setZero()
        base['current_image'] = image

        # Note: I'm hard-coding this to take in world_pos.  I think this is the only way this
        # class is useful, so that should be fine.  But make sure the config isn't giving
        # image_pos directly.
        if 'image_pos' in config or 'world_pos' not in config:
            raise galsim.GalSimConfigValueError(
                "WideScattered requires positions to be given by world_pos")

        # The border in arcsec within which we use the normal skip functionality that creates
        # the stamp for the object to see if there is any overlap on the full image.
        # Things outside this border are skipped before even getting to the StampBuilder.
        if 'border' in config:
            border = galsim.config.ParseValue(config, 'border', base, float)[0]
        else:
            border = 60  # default = 1 arcmin

        # Note: I'm hard-coding this to celestial coordinates.  So just raise an exception if
        # someone does this with a EuclideanWCS
        assert wcs.isCelestial()

        # Find the bounding polynomial in ra, dec.
        # Note: a rectangle in image coordinates is not necessarily a rectangle in ra, dec,
        # since it could be rotated.  Also, it's slightly a trapezoid because of the cos(dec)
        # factor along the ra direction, even if telescope is equitoral mount.
        ll = wcs.toWorld(galsim.PositionD(image.xmin, image.ymin))  # lower-left
        ul = wcs.toWorld(galsim.PositionD(image.xmin, image.ymax))  # upper-left
        lr = wcs.toWorld(galsim.PositionD(image.xmax, image.ymin))  # lower-right
        ur = wcs.toWorld(galsim.PositionD(image.xmax, image.ymax))  # upper-right
        cen = wcs.toWorld(image.true_center)
        #print('ll = ',ll)
        #print('ul = ',ul)
        #print('lr = ',lr)
        #print('ur = ',ur)

        # Push all the corners out by a distance of border
        ll = ll.greatCirclePoint(cen, -border * coord.arcsec)
        ul = ul.greatCirclePoint(cen, -border * coord.arcsec)
        lr = lr.greatCirclePoint(cen, -border * coord.arcsec)
        ur = ur.greatCirclePoint(cen, -border * coord.arcsec)
        #print('ll => ',ll)
        #print('ul => ',ul)
        #print('lr => ',lr)
        #print('ur => ',ur)

        # Directed edges going around the perimeter
        edges = ( (ll,ul), (ul,ur), (ur,lr), (lr,ll) )

        # Find the simple bounding box for trivial rejections
        min_ra = min([ll.ra.deg, ul.ra.deg, lr.ra.deg, ur.ra.deg])
        max_ra = max([ll.ra.deg, ul.ra.deg, lr.ra.deg, ur.ra.deg])
        min_dec = min([ll.dec.deg, ul.dec.deg, lr.dec.deg, ur.dec.deg])
        max_dec = max([ll.dec.deg, ul.dec.deg, lr.dec.deg, ur.dec.deg])
        #print('ra range = ',min_ra,max_ra)
        #print('dec range = ',min_dec,max_dec)

        # Set up rng.
        # Note: This uses the rng of the first object.  Not switching each time.
        # I think that's preferable so we don't get dominated by rng setup for each object.
        # But it means that we need to write stamp.world_pos as a list of these values.
        base['index_key'] = 'obj_num'
        seed = galsim.config.SetupConfigRNG(base, seed_offset=1, logger=logger)
        logger.debug('obj %d: seed = %d',obj_num,seed)

        # Figure out which ones are actually worth building stamps for:
        skip = np.ones(self.nobjects, dtype=bool)
        stamp_world_pos = []  # Keep track of the world_pos values.
        #print('config = ',galsim.config.CleanConfig(config))
        for k in range(self.nobjects):
            base['obj_num'] = obj_num + k
            pos = galsim.config.ParseWorldPos(config, 'world_pos', base, logger)
            stamp_world_pos.append(pos)
            #print('pos = ',pos.ra.deg,pos.dec.deg)

            # Trivial check first.
            if pos.ra.deg < min_ra: continue
            if pos.ra.deg > max_ra: continue
            if pos.dec.deg < min_dec: continue
            if pos.dec.deg > max_dec: continue
            #print('passed trivial checks')

            # Now a more careful check if it is really in the polygon.
            # Check if it is on the same side of all four (directed) edges.
            # Note: The WCS may or may not include a flip, so we don't know whether these
            # should all the left or right.
            lefts = [self._leftside(pos, p1, p2) for p1,p2 in edges]
            #print('lefts = ',lefts)
            if len(set(lefts)) == 2: continue
            #print('all left or all right')

            # OK.  This one is close enough to generate the stamp.
            skip[k] = False

        # Write the stamp-level world_pos to just read off values from the list.
        base['stamp']['world_pos'] = {
            'type' : 'List',
            'items' : stamp_world_pos
        }

        # Tell the stamp builder which items to trivially skip.
        base['stamp']['quick_skip'] = {
            'type' : 'List',
            'items' : skip
        }
        #print('stamp.world_pos = ',stamp_world_pos)
        #print('quick_skip = ',skip)

        # The rest of this just copies from the normal Scattered buildImage function
        stamps, current_vars = galsim.config.stamp.BuildStamps(
                self.nobjects, base, logger=logger, obj_num=obj_num, do_noise=False)

        base['index_key'] = 'image_num'

        for stamp in stamps:
            # This is our signal that the object was skipped.
            if stamp is None: continue
            bounds = stamp.bounds & image.bounds
            logger.debug('image %d: full bounds = %s',image_num,str(image.bounds))
            logger.debug('image %d: stamp bounds = %s',image_num,str(stamp.bounds))
            logger.debug('image %d: Overlap = %s',image_num,str(bounds))
            if bounds.isDefined():
                image[bounds] += stamp[bounds]
            else:
                logger.info(
                    "Object centered at (%d,%d) is entirely off the main image, "
                    "whose bounds are (%d,%d,%d,%d)."%(
                        stamp.center.x, stamp.center.y,
                        image.bounds.xmin, image.bounds.xmax,
                        image.bounds.ymin, image.bounds.ymax))

        # Bring the image so far up to a flat noise variance
        current_var = galsim.config.FlattenNoiseVariance(
                base, image, stamps, current_vars, logger)

        return image, current_var

    @staticmethod
    def _leftside(pos, p1, p2):
        # Check if pos is to the left of the directed edge from p1 to p2.
        # i.e. whether (p1 x p2) . pos is positive.
        # This is calculated efficiently by the _triple method of CelestialCoord
        pos._set_aux()
        p1._set_aux()
        p2._set_aux()
        return pos._triple(p2,p1)

    def add_border(self, pos, center, border):
        """Extend the great circle from ``center`` -> ``pos`` by and additional angle ``border``.
        """

        # Define u = pos
        #        v = center
        #        w = (u x v) x u
        # The great circle through u and v is then
        #
        #   R(t) = u cos(t) + w sin(t)
        #
        # We want the point at R(-border)
        pos._set_aux()
        center._set_aux()
        dsq = (pos._x-center._x)**2 + (pos._y-center._y)**2 + (pos._z-center._z)**2

        # These are unnormalized yet.
        wx = center._x - pos._x + pos._x * dsq/2.
        wy = center._y - pos._y + pos._y * dsq/2.
        wz = center._z - pos._z + pos._z * dsq/2.

        # Normalize
        wr = (wx**2 + wy**2 + wz**2)**0.5
        wx /= wr
        wy /= wr
        wz /= wr

        # R(-border)
        s, c = border.sincos()
        rx = pos._x * c - wx * s
        ry = pos._y * c - wy * s
        rz = pos._z * c - wz * s
        return coord.CelestialCoord.from_xyz(rx,ry,rz)


galsim.config.RegisterImageType('WideScattered', WideScatteredBuilder())
