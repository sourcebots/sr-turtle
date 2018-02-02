from collections import namedtuple

# Points
# TODO: World Coordinates
PolarCoord = namedtuple("PolarCoord", "distance_meters rot_y_rad rot_y_deg")
CartCoord = namedtuple("CartCoord", "x y z")

# Marker class
MarkerBase = namedtuple("Marker",
                        "id size polar pixel_centre cartesian is_wall_marker is_token_marker")


class Marker(MarkerBase):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __str__(self):
        return "Marker {}, pos: ({},{})".format(self.id, self.polar.distance_meters, self.polar.rot_y_rad)
