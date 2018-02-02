from .game_object import GameObject

import pypybox2d


class Token(GameObject):
    grabbable = True

    def __init__(self, arena, damping, marker_id=None):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      linear_damping=damping,
                                                      angular_damping=damping,
                                                      type=pypybox2d.body.Body.DYNAMIC)
        super(Token, self).__init__(arena)
        self.marker_id = marker_id
        self.grabbed = False
        WIDTH = 0.08
        self._body.create_polygon_fixture([(-WIDTH, -WIDTH),
                                           (WIDTH, -WIDTH),
                                           (WIDTH,  WIDTH),
                                           (-WIDTH,  WIDTH)],
                                          density=1,
                                          restitution=0.2,
                                          friction=0.3)

    @property
    def location(self):
        return self._body.position

    @location.setter
    def location(self, new_pos):
        self._body.position = new_pos

    @property
    def heading(self):
        return self._body.angle

    @heading.setter
    def heading(self, new_heading):
        self._body.angle = new_heading

    def grab(self):
        self.grabbed = True

    def release(self):
        self.grabbed = False

    @property
    def surface_name(self):
        return 'sb/token{0}.png'.format('_grabbed' if self.grabbed else '')


class WallMarker(GameObject):
    surface_name = 'sb/wall_marker.png'

    def __init__(self, arena, marker_id, location=(0, 0), heading=0):
        super(WallMarker, self).__init__(arena)
        self.marker_id = marker_id
        self.location = location
        self.heading = heading
