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

WALL_DIAMETER_METRES = 1.2


class Wall(GameObject):
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

        point_dist = WALL_DIAMETER_METRES / 2
        self._body.create_polygon_fixture([(-point_dist, -point_dist),
                                           (point_dist, -point_dist),
                                           (point_dist, point_dist),
                                           (-point_dist, point_dist)],
                                          restitution=0.2,
                                          friction=0.3)
        super(Wall, self).__init__(arena)

class Scavengers(Arena):
    size = (8.4, 8.4)
    start_locations = [(-3.8, -3.8),
                       (3.8, 3.8)]

    start_headings = [pi / 2,
                      -pi / 2]

    wall_locations = [
        # Edge walls
        (-3.6, 0), (3.6, 0), (0, -3.6), (0, 3.6),
        # Center wall
        (-0.6, -0.6), (-0.6, 0.6), (0.6, -0.6), (0.6, 0.6),
    ]

    possible_token_locations = [
        (4.2-3.0, 4.2-0.7),
        (4.2-2.1, 4.2-0.9),
        (4.2-1.4, 4.2-1.4),
        (4.2-0.9, 4.2-2.1),
        (4.2-0.7, 4.2-3.0),
    ]

    missing_token_id = random.randint(0,4)
    # Center one is always there.
    if missing_token_id = 2:
        missing_token_id = random.randint(0,4)

    token_locations = possible_token_locations[:missing_token_id] + possible_token_locations[missing_token_id + 1:]

    def __init__(self, objects=None):
        super(Scavengers, self).__init__(objects)
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

    def _init_tokens(self):
        for zone_id in range(4):
            for location in self.token_locations:
                token = Token(self, damping=5)
                token.location = self.rotate(
                    (-(location[0] + 0.15), -(location[1] + 0.15)),
                    zone_id * (math.pi / 2))
                token.heading = 0
                self.objects.append(token)

    def _init_pedestals(self):
        for x, y in self.wall_locations:
            wall = Wall(self)
            wall.location = (x, y)
            self.objects.append(wall)

    def draw_background(self, surface, display):
        super(Scavengers, self).draw_background(surface, display, draw_motif=False)

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

        for x,y in self.wall_locations:
            wall_radius = WALL_DIAMETER_METRES / 2
            line((x - wall_radius, y - wall_radius), (x + wall_radius, y - wall_radius))
            line((x - wall_radius, y + wall_radius), (x + wall_radius, y + wall_radius))
            line((x - wall_radius, y - wall_radius), (x - wall_radius, y + wall_radius))
            line((x + wall_radius, y - wall_radius), (x + wall_radius, y + wall_radius))

        floor_marking_colour = (0x50, 0x50, 0xC0)
        # Scoring Zone Squares
        line_all_corners((0, 0), (0, 2.4), colour=floor_marking_colour)
        line_all_corners((-2.4, -2.4), (2.4, -2.4), colour=floor_marking_colour)

        # Starting zones
        line_all_corners((3.2, 3.2), (3.2, 4.2), colour=floor_marking_colour)
        line_all_corners((-3.2, 3.2), (-3.2, 4.2), colour=floor_marking_colour)

