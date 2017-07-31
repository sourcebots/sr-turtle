import six
import math
import yaml
import threading
import argparse

# Begin Python 3 compatibility hax

import functools
import pypybox2d.shapes

pypybox2d.shapes.reduce = functools.reduce

# End Python 3 compatibility hax

from sb.robot import *

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config',
                    type=argparse.FileType('r'),
                    default='games/tcr.yaml')
parser.add_argument('robot_scripts',
                    nargs='*')
args = parser.parse_args()


def read_file(fn):
    with open(fn, 'r') as f:
        return f.read()


robot_scripts = args.robot_scripts

# Ask if they didn't just give us them
prompt = "Enter the names of the Python files to run, separated by commas: "
while not robot_scripts:
    robot_script_names = input(prompt).split(',')
    if robot_script_names == ['']:
        continue
    robot_scripts = [s.strip() for s in robot_script_names]

with args.config as f:
    config = yaml.load(f)

sim = Simulator(config, background=False)


## BEGIN SMALLPEICE HACKS

class Motor(object):
    def __init__(self, robot, channel):
        self.robot = robot
        self.channel = channel

    def __str__(self):
        return "Motor({})".format(self.channel)

    __repr__ = __str__

    VOLTAGE_SCALE = 1

    def _get_channel(self):
        motor_board = self.robot.sim_robot.motors[0]

        if self.channel == 0:
            return motor_board.m0
        else:
            return motor_board.m1

    @property
    def voltage(self):
        return self.VOLTAGE_SCALE * (self._get_channel().power / 100)

    @voltage.setter
    def voltage(self, new_voltage):
        new_power = 100 * (new_voltage / self.VOLTAGE_SCALE)
        self._get_channel().power = new_power

class MotorBoard(object):
    def __init__(self, robot):
        self.robot = robot
        self.m0 = Motor(self.robot, 0)
        self.m1 = Motor(self.robot, 1)

    def __str__(self):
        return "MotorBoard"

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

        result = self.robot.sim_robot.send_ultrasound_ping(angle_offset)

        if result is None:
            # No detection is equivalent to just not getting an echo response
            result = 0.0

        return result

class MockedRobot(object):
    def __init__(self, sim_robot):
        self.sim_robot = sim_robot
        self.motor_board = MotorBoard(self)
        self.servo_board = ServoBoard(self)

    def __str__(self):
        return "Robot"

    __repr__ = __str__

    @property
    def motor_boards(self):
        return {'bees': self.motor_board}

    @property
    def servo_boards(self):
        return {'bees': self.motor_board}



## END SMALLPEICE HACKS


class RobotThread(threading.Thread):
    def __init__(self, zone, script, *args, **kwargs):
        super(RobotThread, self).__init__(*args, **kwargs)
        self.zone = zone
        self.script = script
        self.daemon = True

    def run(self):
        def robot():
            with sim.arena.physics_lock:
                robot_object = SimRobot(sim)
                robot_object.zone = self.zone
                robot_object.location = sim.arena.start_locations[self.zone]
                robot_object.heading = sim.arena.start_headings[self.zone]
                return MockedRobot(robot_object)

        six.exec_(open(self.script).read(), {'Robot': robot})


threads = []
for zone, robot in enumerate(robot_scripts):
    thread = RobotThread(zone, robot)
    thread.start()
    threads.append(thread)

sim.run()

# Warn PyScripter users that despite the exit of the main thread, the daemon
# threads won't actually have gone away. See commit 8cad7add for more details.
threads = [t for t in threads if t.is_alive()]
if threads:
    print(
        ("WARNING: {0} robot code threads still active.".format(len(threads))))
    #####                                                               #####
    # If you see the above warning in PyScripter and you want to kill your  #
    # robot code you can press Ctrl+F2 to re-initialize the interpreter and #
    # stop the code running.                                                #
    #####                                                               #####
