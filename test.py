from sbot import *
from math import pi
import time

r = Robot()

motor_board = r.motor_board

grabbed = False

while True:
    motor_board.motors[0] = 1
    motor_board.motors[1] = 1
    print(r.arduino.ultrasound_sensors[6, 7].distance())
    time.sleep(0.75)