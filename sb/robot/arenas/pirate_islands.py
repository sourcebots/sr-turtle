# Arena definition for 'Pirate Islands', the 2018 SourceBots game.
import random
from math import pi, cos, sin

import math

import pygame
import pypybox2d

from sb.robot.game_specific import TOKEN_ZONE_3, TOKEN_ZONE_2, TOKEN_ZONE_1, TOKEN_ZONE_0
from sb.robot.arenas import Arena
from sb.robot.arenas.arena import ARENA_MARKINGS_COLOR, ARENA_MARKINGS_WIDTH
from sb.robot.markers import Token
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
    def heading(self, _new_heading):
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
                if not positions or min(dist(pos, other) for other in positions)\
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
