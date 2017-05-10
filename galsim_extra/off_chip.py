import galsim
import math

def OffChip(config, base, value_type):
    """See if an object should be skipped because it is too far off the edge of a chip
    """
    pos = base['stamp_center']
    bounds = base['current_image'].bounds
    min_dist = galsim.config.ParseValue(config,'min_dist',base,float)[0]
    # Round up to an integer
    min_dist = int(math.ceil(min_dist))

    bounds = bounds.withBorder(min_dist)
    return not bounds.includes(pos)

galsim.config.RegisterValueType('OffChip', OffChip, [ bool ])

