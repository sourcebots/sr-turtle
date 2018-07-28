# Arena definition for 'Tin Can Rally', the 2017 Smallpeice game.
# (A blatant rip-off of the 2011 game from Student Robotics)
from math import pi

import pygame
import pypybox2d

from sb.robot.arenas import Arena
from sb.robot.arenas.arena import ARENA_MARKINGS_COLOR, ARENA_MARKINGS_WIDTH
from sb.robot.display import get_surface
from ..game_object import GameObject

WALL_DIAMETER_METRES = 4


class TCRWall(GameObject):
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
        super().__init__(arena)


class Token(GameObject):
    grabbable = True

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

    def __init__(self, arena, number, damping):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      linear_damping=damping,
                                                      angular_damping=damping*2,
                                                      type=pypybox2d.body.Body.DYNAMIC)
        super(Token, self).__init__(arena)
        self.grabbed = False
        WIDTH = 0.08
        self._body.create_polygon_fixture([(-WIDTH, -WIDTH),
                                           (WIDTH, -WIDTH),
                                           (WIDTH,  WIDTH),
                                           (-WIDTH,  WIDTH)],
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


class TCRArena(Arena):
    start_locations = [(-3.6, -3.6),
                       (3.6, 3.6)]

    start_headings = [pi / 2,
                      -pi / 2]

    def __init__(self, objects=None):
        super().__init__(objects)
        self._init_walls()
        self._init_tokens()

    def _init_tokens(self):
        # Clockwise from top left
        token_locations = [
            (-0.5, -3),
            (3, -3),
            (3, -0.5),
            (0.5, 3),
            (-3, 3),
            (-3, 0.5),
        ]

        for i, location in enumerate(token_locations):
            token = Token(self, i, damping=5)
            token.location = location
            token.heading = 0
            self.objects.append(token)

    def _init_walls(self):
        wall_locations = [(0, 0)]
        for x, y in wall_locations:
            wall = TCRWall(self)
            wall.location = (x, y)
            self.objects.append(wall)

    def draw_background(self, surface, display):
        super().draw_background(surface, display)

        def line(start, end, colour=ARENA_MARKINGS_COLOR, width=ARENA_MARKINGS_WIDTH):
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

        # Section lines
        line_symmetric((0, WALL_DIAMETER_METRES/2), (0, 4))

        # Starting zones
        line_opposite((3, 3), (3, 4))
        line_opposite((3, 3), (4, 3))

        # Centre Wall
        point_dist = (WALL_DIAMETER_METRES / 2)
        line_symmetric(
            (point_dist, point_dist), (-point_dist, point_dist), colour=(0x00, 0x80, 0xd6), width=7)
