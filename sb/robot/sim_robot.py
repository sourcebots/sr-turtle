import time
from math import pi, sin, cos, degrees, hypot, atan2, radians

from .game_object import GameObject

import pypybox2d

SPEED_SCALE_FACTOR = 0.02
MAX_MOTOR_SPEED = 100

GRAB_RADIUS = 0.4
HALF_GRAB_SECTOR_WIDTH = pi / 4
HALF_FOV_WIDTH = pi / 6

GRABBER_OFFSET = 0.25


class AlreadyHoldingSomethingException(Exception):
    def __str__(self):
        return "The robot is already holding something."


class MotorChannel(object):
    def __init__(self, robot):
        self._power = 0
        self._robot = robot

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        value = min(max(value, -MAX_MOTOR_SPEED), MAX_MOTOR_SPEED)
        with self._robot.lock:
            self._power = value


class Motor:
    """Represents a motor board."""
    # This is named `Motor` instead of `MotorBoard` for consistency with pyenv

    def __init__(self, robot):
        self._robot = robot
        self.serialnum = "SIM_MBv4"

        self.m0 = MotorChannel(robot)
        self.m1 = MotorChannel(robot)

    def __repr__(self):
        return "Motor( serialnum = \"{0}\" ) (Simulated Motor Board v4)" \
               .format(self.serialnum)


class SimRobot(GameObject):
    width = 0.45

    surface_name = 'sb/robot.png'

    _holding = None

    ## Constructor ##

    @property
    def location(self):
        with self.lock:
            return self._body.position

    @location.setter
    def location(self, new_pos):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        with self.lock:
            self._body.position = new_pos

    @property
    def heading(self):
        with self.lock:
            return self._body.angle

    @heading.setter
    def heading(self, _new_heading):
        if self._body is None:
            return  # Slight hack: deal with the initial setting from the constructor
        with self.lock:
            self._body.angle = _new_heading

    def send_ultrasound_ping(self, angle_offset):
        with self.arena.physics_lock:
            world = self._body.world

            centre_point = self._body.world_center

            spread_casts = 10
            spread_maximum_angle_radians = radians(10)

            cast = []
            cast_range = 4.0

            for spread_offset in [
                spread_maximum_angle_radians * (x / spread_casts)
                for x in range(-spread_casts, spread_casts + 1)
            ]:
                cast_angle = self._body.angle + angle_offset + spread_offset

                target_point = [
                    centre_point[0] + cast_range * cos(cast_angle),
                    centre_point[1] + cast_range * sin(cast_angle),
                ]

                cast.extend(world.ray_cast(centre_point, target_point))

        if not cast:
            return None

        # Sort by fraction along the ray
        cast.sort(key=lambda x: x[3])

        fixture, intercept_point, _, fraction = cast[0]

        distance_to_intercept = fraction * cast_range

        return distance_to_intercept

    def __init__(self, simulator):
        self._body = None
        self.zone = 0
        super(SimRobot, self).__init__(simulator.arena)
        self.motors = [Motor(self)]
        make_body = simulator.arena._physics_world.create_body
        half_width = self.width * 0.5
        with self.arena.physics_lock:
            self._body = make_body(position=(0, 0),
                                   angle=0,
                                   linear_damping=0.0,
                                   angular_damping=0.0,
                                   type=pypybox2d.body.Body.DYNAMIC)
            self._body.create_polygon_fixture([(-half_width, -half_width),
                                               (half_width, -half_width),
                                               (half_width,  half_width),
                                               (-half_width,  half_width)],
                                              density=500 * 0.12)  # MDF @ 12cm thickness
        simulator.arena.objects.append(self)

    ## Internal methods ##

    def _apply_wheel_force(self, y_position, power):
        location_world_space = self._body.get_world_point((0, y_position))
        force_magnitude = power * 0.6
        # account for friction
        frict_world = self._body.get_linear_velocity_from_local_point(
            (0, y_position))
        frict_x, frict_y = self._body.get_local_vector(frict_world)
        force_magnitude -= frict_x * 50.2
        force_world_space = (force_magnitude * cos(self.heading),
                             force_magnitude * sin(self.heading))
        self._body.apply_force(force_world_space, location_world_space)

    ## "Public" methods for simulator code ##

    def tick(self, time_passed):
        with self.lock, self.arena.physics_lock:
            half_width = self.width * 0.5
            # left wheel
            self._apply_wheel_force(-half_width, self.motors[0].m0.power)
            # right wheel
            self._apply_wheel_force(half_width, self.motors[0].m1.power*1.05)
            # kill the lateral velocity
            right_normal = self._body.get_world_vector((0, 1))
            lateral_vel = (right_normal.dot(self._body.linear_velocity) *
                           right_normal)
            impulse = self._body.mass * -lateral_vel
            self._body.apply_linear_impulse(impulse, self._body.world_center)

    ## "Public" methods for user code ##

    def grab(self):
        if self._holding is not None:
            raise AlreadyHoldingSomethingException()

        with self.lock:
            x, y = self.location
            heading = self.heading

        def object_filter(o):
            rel_x, rel_y = (o.location[0] - x, o.location[1] - y)
            direction = atan2(rel_y, rel_x)
            return (o.grabbable and
                    hypot(rel_x, rel_y) <= GRAB_RADIUS and
                    -HALF_GRAB_SECTOR_WIDTH < direction - heading < HALF_GRAB_SECTOR_WIDTH and
                    not o.grabbed)

        objects = list(filter(object_filter, self.arena.objects))
        if objects:
            self._holding = objects[0]
            if hasattr(self._holding, '_body'):
                with self.lock, self.arena.physics_lock:
                    self._holding_joint = self._body._world.create_weld_joint(self._body,
                                                                              self._holding._body,
                                                                              local_anchor_a=(
                                                                                  GRABBER_OFFSET, 0),
                                                                              local_anchor_b=(0, 0))
            self._holding.grab()
            return True
        else:
            return False

    def release(self):
        if self._holding is not None:
            self._holding.release()
            if hasattr(self._holding, '_body'):
                with self.lock, self.arena.physics_lock:
                    self._body.world.destroy_joint(self._holding_joint)
                self._holding_joint = None
            self._holding = None
            return True
        else:
            return False
