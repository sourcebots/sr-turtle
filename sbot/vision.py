from __future__ import division

from collections import namedtuple

# Points
# TODO: World Coordinates

# all floats
PolarCoord = namedtuple(
    'PolarCoord',
    {'distance_meters', 'rot_y_rad', 'rot_y_deg'},
)
# distance_meters: float
# rot_y_rad: float
# rot_y_deg: float

CartCoord = namedtuple(
    'CartCoord',
   {'x', 'y', 'z'},
)
# x: float
# y: float
# z: float

MarkerTuple = namedtuple(
    'Marker',
    {'id', 'size', 'polar', 'is_wall_marker', 'is_token_marker'}
)
# id: int
# size: float
# polar: PolarCoord
# is_wall_marker: Callable[[], bool]
# is_token_marker: Callable[[], bool]

class Marker(MarkerTuple):
    __slots__ = ()

    def __str__(self):
        return "Marker {}, pos: ({},{})".format(self.id, self.polar.distance_meters,
                                                self.polar.rot_y_rad)
