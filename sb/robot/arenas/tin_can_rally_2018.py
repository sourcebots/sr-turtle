# Arena definition for 'Tin Can Rally', the 2018 Smallpeice game.
# (A blatant rip-off of the 2011 game from Student Robotics)
from math import pi, cos, sin

import pygame
import pypybox2d

from sb.robot.arenas import Arena
from sb.robot.arenas.arena import ARENA_MARKINGS_COLOR, ARENA_MARKINGS_WIDTH
from ..game_object import GameObject

WALL_DIAMETER_METRES = 4


class TCRWall(GameObject):
    @property
    def location(self):
        return self._body.position

    @location.setter
    def location(self, new_pos):
        self._body.position = (
        new_pos[0] - 4 + self.width / 2, new_pos[1] - 4 + self.height / 2)

    @property
    def heading(self):
        return self._body.angle

    @property
    def width(self):
        return self._w

    @property
    def height(self):
        return self._h

    @heading.setter
    def heading(self, new_heading):
        self._body.angle = new_heading

    def __init__(self, arena, dims, pos=(0.0, 0.0)):
        self._body = arena._physics_world.create_body(position=(0.0, 0.0),
                                                      angle=0,
                                                      type=pypybox2d.body.Body.STATIC)
        hw = dims[0] / 2.0
        hh = dims[1] / 2.0
        fixture = self._body.create_polygon_fixture([
            (-hw, -hh),
            (hw, -hh),
            (hw, hh),
            (-hw, hh)],
            restitution=0.2,
            friction=0.3)
        self.vertices = fixture.shape.vertices
        self._w = dims[0]
        self._h = dims[1]
        self.location = pos
        super().__init__(arena)

    def get_corners(self):
        return [(x + self.location[0], y + self.location[1]) for x, y in self.vertices]


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

    def __init__(self, arena, damping, is_gold=False):
        self._body = arena._physics_world.create_body(position=(0, 0),
                                                      angle=0,
                                                      linear_damping=damping,
                                                      angular_damping=damping * 2,
                                                      type=pypybox2d.body.Body.DYNAMIC)
        super(Token, self).__init__(arena)
        self.grabbed = False
        WIDTH = 0.08
        self._body.create_circle_fixture(
            radius=WIDTH,
            restitution=0.2,
            friction=0.3
        )
        self.is_gold = is_gold

    def grab(self):
        self.grabbed = True

    def release(self):
        self.grabbed = False

    @property
    def surface_name(self):
        return 'sb/{}can{}.png'.format('gold' if self.is_gold else '',
                                       '_grabbed' if self.grabbed else '')


class TCRArena2018(Arena):
    start_locations = [(-4 + 2.5, -4 + 0.8),
                       (4 - 2.5, 4 - 0.8)]

    start_headings = [-pi, 0]

    def __init__(self, objects=None):
        super().__init__(objects)
        self._init_walls()
        self._init_tokens()

    def _init_tokens(self):
        token_locations = [
            # Numbers from the SVG defined in the rules.
            (0.5 - 4, 0.8 - 4),
            (1.2 - 4, 3.7 - 4),
            (2.0 - 4, 7.7 - 4),
            (3.4 - 4, 6.0 - 4),
        ]

        token_locations += [TCRArena2018.rotate(pos, pi) for pos in token_locations]

        for location in token_locations:
            token = Token(self, damping=5)
            token.location = location
            token.heading = 0
            self.objects.append(token)

        gold_token = Token(self, damping=5, is_gold=True)
        self.objects.append(gold_token)

    @staticmethod
    def reflect(pos):
        centred = (pos[0] - 4, pos[1] - 4)
        rotated = TCRArena2018.rotate(centred, pi)
        return rotated[0] + 4, rotated[1] + 4

    @staticmethod
    def rotate(pos, ang):
        """
        Rotate given vector around the centre by the given angle
        :param pos: vector to rotate
        :param ang: angle to rotate
        :return:
        """
        return cos(ang) * pos[0] - sin(ang) * pos[1], sin(ang) * pos[0] + cos(
            ang) * pos[1]

    def _init_walls(self):
        self.walls = set()
        wall_details = {
            # Copied from the SVG spec, tweaked slightly because it didn't match up.
            ((1.20, 2.40), (1.50, 1.55)),
            ((1.20, 2.40), (2.68, 1.55)),
            ((1.22, 1.22), (5.28, 1.55)),
        }
        obstacle_details = {
            ((0.2, 0.2), (1.50, 3.95)),
            ((0.2, 0.2), (1.50, 5.02)),
            ((0.2, 0.2), (2.45, 4.57)),
            ((0.2, 0.2), (2.72, 5.23)),
        }
        walls = {TCRWall(self, pos[0], pos[1]) for pos in wall_details}
        obstacles = {TCRWall(self, pos[0], pos[1]) for pos in obstacle_details}

        def rotate(pos):
            return self.reflect((pos[1][0] + pos[0][0], pos[1][1] + pos[0][1]))

        rotated_walls = {TCRWall(self, pos[0], rotate(pos)) for pos in wall_details}
        rotated_obstacles = {TCRWall(self, pos[0], rotate(pos))
                             for pos in obstacle_details}

        self.walls = walls.union(rotated_walls)
        self.obstacles = obstacles.union(rotated_obstacles)

        [self.objects.append(wall) for wall in self.walls]
        [self.objects.append(obstacle) for obstacle in self.obstacles]

    def draw_background(self, surface, display):
        super().draw_background(surface, display, draw_motif=False)

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
        colour = (0x70, 0x70, 0x70)
        # Straight lines
        line_opposite((1.5 - 4, 0 - 4), (1.5 - 4, 1.55 - 4), colour=colour)
        line_opposite((6.5 - 4, 4.1 - 4), (8 - 4, 4.1 - 4), colour=colour)
        # The bendy boundary
        start = (5.28 - 4, 0 - 4)
        p1 = (start[0], start[1] + 1.25)
        p2 = (p1[0] - 0.3, p1[1] + 0.3)
        end = (p2[0] - 1.04, p2[1])

        line_opposite(start, p1, colour=colour)
        line_opposite(p1, p2, colour=colour)
        line_opposite(p2, end, colour=colour)

        # Centre Wall
        for wall in self.walls:
            vectors = wall.get_corners()
            colour = (0x2d, 0x8b, 0xff)
            pygame.draw.polygon(surface, colour, [display.to_pixel_coord(pos) for pos in vectors])

        # Draw the motif on the bottom of the screen
        self.draw_motif(surface, display, (0.5, 3.25))


        for obstacle in self.obstacles:
            vectors = obstacle.get_corners()
            colour = (0xff, 0x44, 0x44)
            pygame.draw.polygon(surface, colour, [display.to_pixel_coord(pos) for pos in vectors])
