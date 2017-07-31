from math import pi
import time

R = Robot()

motor_board = R.motors[0]

while True:
    distance_right = R.send_ultrasound_ping(pi / 2) or 4.0
    distance_ahead = R.send_ultrasound_ping(0) or 4.0

    print("Forward distance: ", distance_ahead)

    if distance_ahead < 1.0:
        motor_board.m0.power = -50
        motor_board.m1.power = 50
        print("COLLISION AVOID")
    else:
        target_distance = 0.8
        distance_error = distance_right - target_distance

        print("Tracking error: ", distance_error, " - measured: ", distance_right)

        motor_board.m0.power = 50
        motor_board.m1.power = 50 - 35*distance_error

    time.sleep(0.1)
