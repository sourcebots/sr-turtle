import time
from collections import namedtuple
from math import pi, sin, cos, degrees, hypot, atan2, radians

import math

from .game_object import GameObject
from .vision import Marker, PolarCoord
from .game_specific import MARKER_SIZES, WALL, TOKEN

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


BRAKE = 0  # 0 so setting the motors to 0 has exactly the same affect as setting the motors to BRAKE
COAST = "coast"


class MotorBoard(object):
    VOLTAGE_SCALE = 1

    def __init__(self, robot):
        self.robot = robot
        self._motors = [0,0]

    def __str__(self):
        return "MotorBoard"

    def _check_voltage(self,new_voltage):
        if new_voltage != COAST and (new_voltage > 1 or new_voltage < -1):
            raise ValueError(
                'Incorrect voltage value, valid values: between -1 and 1, robot.COAST, or robot.BRAKE')

    @property
    def m0(self):
        return self._motors[0]

    @m0.setter
    def m0(self, new_voltage):
        self._check_voltage(new_voltage)
        self._motors[0] = new_voltage

    @property
    def m1(self):
        return self._motors[1]

    @m1.setter
    def m1(self, new_voltage):
        self._check_voltage(new_voltage)
        self._motors[1] = new_voltage

    __repr__ = __str__


class ServoBoard(object):
    def __init__(self, robot):
        self.robot = robot

    def __str__(self):
        return "ServoBoard"

    __repr__ = __str__

    ULTRASOUND_ANGLES = {
        (6, 7): ('ahead', 0),
        (8, 9): ('right', math.pi / 2),
        (10, 11): ('left', -math.pi / 2),
    }

    def read_ultrasound(self, trigger_pin, echo_pin):
        pin_pair = (trigger_pin, echo_pin)

        try:
            _, angle_offset = self.ULTRASOUND_ANGLES[pin_pair]
        except KeyError:
            print("There's no ultrasound module on those pins. Try:")
            for (
                    (trigger_pin, echo_pin),
                    (direction, _),
            ) in self.ULTRASOUND_ANGLES.items():
                print("Pins {} and {} for the sensor pointing {}".format(
                    trigger_pin,
                    echo_pin,
                    direction,
                ))
            return 0.0

        result = self.robot.send_ultrasound_ping(angle_offset)

        if result is None:
            # No detection is equivalent to just not getting an echo response
            result = 0.0

        return result


class Camera:
    def __init__(self, robot):
        self.robot = robot

    def __str__(self):
        return "Camera"

    def see(self):
        with self.robot.lock:
            x, y = self.robot.location
            heading = self.robot.heading

        acq_time = time.time()
        # Block for a realistic amount of time
        time.sleep(0.2)

        MOTION_BLUR_SPEED_THRESHOLD = 5

        def robot_moving(robot):
            vx, vy = robot._body.linear_velocity
            return hypot(vx, vy) > MOTION_BLUR_SPEED_THRESHOLD

        def motion_blurred(o):
            # Simple approximation: we can't see anything if either it's moving
            # or we're moving. This doesn't handle tokens grabbed by other robots
            # but Sod's Law says we're likely to see those anyway.
            return (robot_moving(self.robot) or
                    isinstance(o, SimRobot) and robot_moving(o))

        def object_filter(o):
            # Choose only marked objects within the field of view
            direction = atan2(o.location[1] - y, o.location[0] - x)
            return (o.marker_id is not None and
                    o is not self and
                    -HALF_FOV_WIDTH < direction - heading < HALF_FOV_WIDTH and
                    not motion_blurred(o))

        def is_wall_marker(marker_id):
            return marker_id in WALL

        def is_token_marker(marker_id):
            return marker_id in TOKEN

        def marker_map(o):
            # Turn a marked object into a Marker
            rel_x, rel_y = (o.location[0] - x, o.location[1] - y)
            rot_y = atan2(rel_y, rel_x) - heading
            polar_coord = PolarCoord(
                distance_meters=hypot(rel_x, rel_y),
                rot_y_rad=rot_y,
                rot_y_deg=degrees(rot_y)
            )

            # TODO: Check polar coordinates are the right way around
            mid = o.marker_id
            return Marker(
                id=mid,
                size=MARKER_SIZES[mid],
                is_wall_marker=lambda: is_wall_marker(mid),
                is_token_marker=lambda: is_token_marker(mid),
                polar=polar_coord,
                pixel_centre="NOT SUPPORTED",
                cartesian="NOT SUPPORTED",
            )

        return sorted([marker_map(obj) for obj in self.robot.arena.objects if
                object_filter(obj)],key=lambda m:m.polar.distance_meters)

    __repr__ = __str__

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
        self.motors = [MotorBoard(self)]
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
                                               (half_width, half_width),
                                               (-half_width, half_width)],
                                              density=500 * 0.12)  # MDF @ 12cm thickness
        simulator.arena.objects.append(self)
        self.motor_board = MotorBoard(self)
        self.servo_board = ServoBoard(self)
        self.camera = Camera(self)

    def __str__(self):
        return "Robot"

    __repr__ = __str__

    @property
    def motor_boards(self):
        return {'bees': self.motor_board}

    @property
    def servo_boards(self):
        return {'bees': self.motor_board}

    @property
    def cameras(self):
        return {'bees': self.camera}

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

    def _apply_wheel_coast(self, y_position):
        location_world_space = self._body.get_world_point((0, y_position))
        # account for friction
        frict_world = self._body.get_linear_velocity_from_local_point(
            (0, y_position))
        frict_x, frict_y = self._body.get_local_vector(frict_world)
        force = frict_x * -5.2
        force_world_space = (force * cos(self.heading),
                             force * sin(self.heading))
        self._body.apply_force(force_world_space, location_world_space)

    ## "Public" methods for simulator code ##

    def tick(self, time_passed):
        with self.lock, self.arena.physics_lock:
            half_width = self.width * 0.5
            # left wheel
            if self.motor_board.m0 == COAST:
                self._apply_wheel_coast(-half_width)
            else:
                self._apply_wheel_force(-half_width, self.motor_board.m0*100)
            # right wheel
            if self.motor_board.m1 == COAST:
                self._apply_wheel_coast(half_width)
            else:
                self._apply_wheel_force(half_width, self.motor_board.m1*100)
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
                    self._holding_joint = self._body._world.create_weld_joint(
                        self._body,
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
