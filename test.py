from math import pi
import time

r = Robot()

motor_board = r.motor_board

while True:
    distance_right = r.servo_board.read_ultrasound(8, 9)
    distance_ahead = r.servo_board.read_ultrasound(6, 7)

    print("Forward distance: ", distance_ahead)

    if distance_ahead < 1.0:
        motor_board.m0 = -0.5
        motor_board.m1 = 0.5
        print("COLLISION AVOID")
    else:
        target_distance = 0.8
        distance_error = distance_right - target_distance

        print("Tracking error: ", distance_error, " - measured: ", distance_right)

        motor_board.m0 = 0.5
        motor_board.m1 = 0.5 - .35 * distance_error

    time.sleep(0.1)
