# Arena definition for 'Pirate Islands', the 2018 SourceBots game.
from __future__ import division

import random
from math import pi, cos, sin

import math

import pygame
import pypybox2d

from ..game_specific import TOKEN_ZONE_3, TOKEN_ZONE_2, TOKEN_ZONE_1, \
    TOKEN_ZONE_0
from . import Arena
from .arena import ARENA_MARKINGS_COLOR, ARENA_MARKINGS_WIDTH
from ..markers import Token
from ..game_object import GameObject

#######

PEDESTAL_DIAMETER_METERS = 0.3


class Pedestal(GameObject):
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

    def __init__(self, arena):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      type=pypybox2d.body.Body.STATIC)

        point_dist = PEDESTAL_DIAMETER_METERS / 2
        self._body.create_polygon_fixture([(-point_dist, -point_dist),
                                           (point_dist, -point_dist),
                                           (point_dist, point_dist),
                                           (-point_dist, point_dist)],
                                          density=1,
                                          restitution=0.2,
                                          friction=0.3)
        super().__init__(arena)

    surface_name = 'sb/pedestal.png'

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
        Rotate given vector around the origin by the given angle
        :param pos: vector to rotate
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
                if not positions or min(dist(pos, other) for other in positions) \
                        > min_dist:
                    positions.append(pos)
                    break
        return positions

    def _init_tokens(self):
        token_locations = self.random_pos_spaced(4)
        for zone_id, token_ids in enumerate(
                [TOKEN_ZONE_0, TOKEN_ZONE_1, TOKEN_ZONE_2, TOKEN_ZONE_3]):
            for location, token_id in zip(token_locations, token_ids):
                token = Token(self, marker_id=token_id, damping=5)
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

        def line_all_corners(start, end, **kwargs):
            for ang in [0, pi/2, pi, 3/2 * pi]:
                new_start = self.rotate(start, ang)
                new_end = self.rotate(end, ang)
                line(new_start, new_end, **kwargs)

        # Scoring Zone Squares
        line_all_corners((0.15, 0.15), (0.15, 3))
        line_all_corners((-0.15, 0.15), (-0.15, 3))
        line_all_corners((3, 3), (0.15, 3))
        line_all_corners((-3, 3), (-0.15, 3))

        # Inner zone squares
        line_all_corners((-2, 2), (-0.15, 2))
        line_all_corners((2, 2), (0.15, 2))

        # Starting zones
        line_all_corners((3, 3), (3, 4))
        line_all_corners((-3, 3), (-3, 4))
