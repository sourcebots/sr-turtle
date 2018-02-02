from typing import NamedTuple, Callable


# Points
# TODO: World Coordinates


class PolarCoord(NamedTuple):
    distance_meters: float
    rot_y_rad: float
    rot_y_deg: float


class CartCoord(NamedTuple):
    x: float
    y: float
    z: float


class Marker(NamedTuple):
    id: int
    size: float
    polar: PolarCoord
    is_wall_marker: Callable[[], bool]
    is_token_marker: Callable[[], bool]

    def __str__(self):
        return "Marker {}, pos: ({},{})".format(self.id, self.polar.distance_meters, self.polar.rot_y_rad)
