# Arena definition for 'Pirate Islands', the 2018 SourceBots game.
import random
from math import pi, cos, sin

import math
import pygame
import pypybox2d

from sb.robot.arenas import Arena
from sb.robot.arenas.arena import ARENA_MARKINGS_COLOR, ARENA_MARKINGS_WIDTH
from ..game_object import GameObject

WALL = set(range(0, 28))  # 0 - 27

# Currently for SB2018
COLUMN_N = set(range(28, 32))
COLUMN_E = set(range(32, 36))
COLUMN_S = set(range(36, 40))
COLUMN_W = set(range(40, 44))
COLUMN_FACING_N = set(range(28, 44, 4))
COLUMN_FACING_E = set(range(29, 44, 4))
COLUMN_FACING_S = set(range(30, 44, 4))
COLUMN_FACING_W = set(range(31, 44, 4))

# Individual Column faces.
COLUMN_N_FACING_N = (COLUMN_N & COLUMN_FACING_N).pop()
COLUMN_N_FACING_S = (COLUMN_N & COLUMN_FACING_S).pop()
COLUMN_N_FACING_E = (COLUMN_N & COLUMN_FACING_E).pop()
COLUMN_N_FACING_W = (COLUMN_N & COLUMN_FACING_W).pop()

COLUMN_S_FACING_N = (COLUMN_S & COLUMN_FACING_N).pop()
COLUMN_S_FACING_S = (COLUMN_S & COLUMN_FACING_S).pop()
COLUMN_S_FACING_E = (COLUMN_S & COLUMN_FACING_E).pop()
COLUMN_S_FACING_W = (COLUMN_S & COLUMN_FACING_W).pop()

COLUMN_E_FACING_N = (COLUMN_E & COLUMN_FACING_N).pop()
COLUMN_E_FACING_S = (COLUMN_E & COLUMN_FACING_S).pop()
COLUMN_E_FACING_E = (COLUMN_E & COLUMN_FACING_E).pop()
COLUMN_E_FACING_W = (COLUMN_E & COLUMN_FACING_W).pop()

COLUMN_W_FACING_N = (COLUMN_W & COLUMN_FACING_N).pop()
COLUMN_W_FACING_S = (COLUMN_W & COLUMN_FACING_S).pop()
COLUMN_W_FACING_E = (COLUMN_W & COLUMN_FACING_E).pop()
COLUMN_W_FACING_W = (COLUMN_W & COLUMN_FACING_W).pop()

COLUMN = (COLUMN_N | COLUMN_E | COLUMN_S | COLUMN_W)

TOKEN = set(range(44, 64))

TOKEN_ZONE_0 = set(range(44, 49))
TOKEN_ZONE_1 = set(range(49, 54))
TOKEN_ZONE_2 = set(range(54, 59))
TOKEN_ZONE_3 = set(range(59, 64))

# The following constants are used to define the marker sizes

MARKER_SIZES = {}
MARKER_SIZES.update({m: (0.25, 0.25) for m in (WALL | COLUMN)})
MARKER_SIZES.update({m: (0.1, 0.1) for m in TOKEN})

#######

PEDESTAL_DIAMETER_METERS = 0.3


class Pedestal(GameObject):
    @property
    def location(self):
        return self._body.position

    @location.setter
    def location(self, new_pos):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        self._body.position = new_pos

    @property
    def heading(self):
        return self._body.angle

    @heading.setter
    def heading(self, _new_heading):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        self._body.angle = _new_heading

    def __init__(self, arena):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      type=pypybox2d.body.Body.STATIC)

        point_dist = PEDESTAL_DIAMETER_METERS / 2
        self._body.create_polygon_fixture([(-point_dist, -point_dist),
                                           (point_dist, -point_dist),
                                           (point_dist, point_dist),
                                           (-point_dist, point_dist)],
                                          restitution=0.2,
                                          friction=0.3)
        super().__init__(arena)

    @property
    def surface_name(self):
        return 'sb/pedestal.png'


class Token(GameObject):
    grabbable = True

    @property
    def location(self):
        return self._body.position

    @location.setter
    def location(self, new_pos):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        self._body.position = new_pos

    @property
    def heading(self):
        return self._body.angle

    @heading.setter
    def heading(self, _new_heading):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        self._body.angle = _new_heading

    def __init__(self, arena, number, damping):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      linear_damping=damping,
                                                      angular_damping=damping * 2,
                                                      type=pypybox2d.body.Body.DYNAMIC)
        super(Token, self).__init__(arena)
        self.grabbed = False
        WIDTH = 0.08
        self._body.create_polygon_fixture([(-WIDTH, -WIDTH),
                                           (WIDTH, -WIDTH),
                                           (WIDTH, WIDTH),
                                           (-WIDTH, WIDTH)],
                                          density=1,
                                          restitution=0.2,
                                          friction=0.3)

    def grab(self):
        self.grabbed = True

    def release(self):
        self.grabbed = False

    @property
    def surface_name(self):
        return 'sb/token{0}.png'.format('_grabbed' if self.grabbed else '')


class PIArena(Arena):
    start_locations = [(-3.6, -3.6),
                       (3.6, 3.6)]

    start_headings = [pi / 2,
                      -pi / 2]

    def __init__(self, objects=None):
        super().__init__(objects)
        self._init_pedestals()
        self._init_tokens()

    @staticmethod
    def rotate(pos, ang):
        """
        Rotate given position around the origin by the given angle
        :param pos: position to rotate
        :param ang: angle to rotate
        :return:
        """
        return cos(ang) * pos[0] - sin(ang) * pos[1], sin(ang) * pos[0] + cos(
            ang) * pos[1]

    @staticmethod
    def random_pos_spaced(n, min_dist=0.3):
        """ Creates a n position which are guaranteed to be at least
        min_dist away from each other
        """
        positions = []

        def dist(a, b):
            return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

        for _ in range(n):
            while True:
                pos = (
                0.07 + random.random() * 1.7, 0.07 + random.random() * 1.7)
                if not positions or min(
                        [dist(pos, other) for other in positions]) > min_dist:
                    positions.append(pos)
                    break
        return positions

    def _init_tokens(self):
        token_locations = self.random_pos_spaced(4)
        for zone_id, token_ids in enumerate(
                [TOKEN_ZONE_0, TOKEN_ZONE_1, TOKEN_ZONE_2, TOKEN_ZONE_3]):
            for i, (location, token_id) in enumerate(
                    zip(token_locations, token_ids)):
                token = Token(self, token_id, damping=5)
                token.location = self.rotate(
                    (-(location[0] + 0.15), -(location[1] + 0.15)),
                    zone_id * (math.pi / 2))
                token.heading = 0
                self.objects.append(token)

    def _init_pedestals(self):
        wall_locations = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        for x, y in wall_locations:
            wall = Pedestal(self)
            wall.location = (x, y)
            self.objects.append(wall)

    def draw_background(self, surface, display):
        super().draw_background(surface, display)

        def line(start, end, colour=ARENA_MARKINGS_COLOR,
                 width=ARENA_MARKINGS_WIDTH):
            pygame.draw.line(surface, colour,
                             display.to_pixel_coord(
                                 start), display.to_pixel_coord(end),
                             width)

        def line_opposite(start, end, **kwargs):
            start_x, start_y = start
            end_x, end_y = end
            line((start_x, start_y), (end_x, end_y), **kwargs)
            line((-start_x, -start_y), (-end_x, -end_y), **kwargs)

        def line_symmetric(start, end, **kwargs):
            start_x, start_y = start
            end_x, end_y = end
            line_opposite(start, end, **kwargs)
            line_opposite((start_y, start_x), (end_y, end_x), **kwargs)

        # Scoring Zone Squares
        line_symmetric((0.15, 0.15), (0.15, 3))
        line_symmetric((-0.15, 0.15), (-0.15, 3))
        line_symmetric((3, 3), (0.15, 3))
        line_symmetric((-3, 3), (-0.15, 3))

        # Inner zone squares
        line_symmetric((-2, 2), (-0.15, 2))
        line_symmetric((2, 2), (0.15, 2))

        # Starting zones
        line_symmetric((3, 3), (3, 4))
        line_symmetric((-3, 3), (-3, 4))
