from robot import *
from math import pi
import time

r = Robot()

motor_board = r.motor_board

grabbed = False

while True:
    markers = r.camera.see()
    closest_token = None
    for marker in markers:
        if marker.is_token_marker():
            closest_token = marker
            break

    # If we couldn't see a token
    if closest_token is None:
        # Slowly turn in circles until we see one
        motor_board.m0 = -0.05
        motor_board.m1 = 0.05
    else:
        bearing = closest_token.polar.rot_y_deg
        distance = closest_token.polar.distance_meters
        if distance < 0.4:
            if not grabbed:
                print("GRAB")
                r.grab()
                grabbed = True
            motor_board.m0 = COAST
            motor_board.m1 = COAST
        else:
            if bearing < -5:
                # Turn right
                motor_board.m0 = -0.1
                motor_board.m1 = 0.1

            elif bearing > 5:
                # Turn left
                motor_board.m0 = 0.1
                motor_board.m1 = -0.1
            else:
                motor_board.m0 = 0.3
                motor_board.m1 = 0.3


    time.sleep(0.1)
