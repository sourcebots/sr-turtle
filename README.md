Student Robotics Robot Simulator
================================

This is a simple, portable robot simulator developed for [Student Robotics](https://studentrobotics.org), originally for a summer school aimed at 15-18 year olds. It allows competitors to test their code for such things as navigation and item finding while remaining similar to the [Student Robotics API][sr-api] which they are using to control their real hardware.

Installing and running
----------------------

The simulator requires a Python 3.4 installation, the [pygame](http://pygame.org/) library, [PyPyBox2D](https://pypi.python.org/pypi/pypybox2d/2.1-r331), and [PyYAML](https://pypi.python.org/pypi/PyYAML/).

Pygame, unfortunately, can be tricky (though [not impossible](http://askubuntu.com/q/312767)) to install in virtual environments. If you are using `pip`, you might try `pip install hg+https://bitbucket.org/pygame/pygame`, or you could use your operating system's package manager. Windows users could use [Portable Python](http://portablepython.com/). PyPyBox2D and PyYAML are more forgiving, and should install just fine using `pip` or `easy_install`.

Once the dependencies are installed, simply run the `test.py` script to test out the simulator.

## Troubleshooting

When running `python run.py <file>`, you may be presented with an error: `ImportError: No module named 'robot'`. This may be due to a conflict between sr.tools and sr.robot. To resolve, symlink simulator/sr/robot to the location of sr.tools.

On Ubuntu, this can be accomplished by:
* Find the location of srtools: `pip show sr.tools`
* Get the location. In my case this was `/usr/local/lib/python2.7/dist-packages`
* Create symlink: `ln -s path/to/simulator/sr/robot /usr/local/lib/python2.7/dist-packages/sr/`

Writing and running a program
-----------------------------

Keep your programs in the directory containing the simulator files, so that the `sr` module can be imported.

To run one or more scripts in the simulator, use `run.py`, passing it the file names. You can also pass it a configuration [YAML](http://yaml.org/) file with the `--config` switch, which sets the game to be used and other parameters (such as the number of tokens in a Pirate Plunder game).

An example program can be found in `test.py`, which implements a simple state machine and does a pretty shoddy job of finding and picking up tokens. To try it, run the following:

```bash
$ python run.py test.py
```

To pit three test robots against one another, pass the script in three times:

```bash
$ python run.py test.py test.py test.py
```

Robot API
---------

The API for controlling a simulated robot is designed to be as similar as possible to the [SR API][sr-api].

### Motors ###

The simulated robot has two motors configured for skid steering, connected to a two-output [Motor Board](https://studentrobotics.org/docs/kit/motor_board). The left motor is connected to output `0` and the right motor to output `1`.

The Motor Board API is identical to [that of the SR API](https://studentrobotics.org/docs/programming/sr/motors/), except that motor boards cannot be addressed by serial number. So, to turn on the spot at one quarter of full power, one might write the following:

```python
R.motors[0].m0.power = 25
R.motors[0].m1.power = -25
```

### The Grabber ###

The robot is equipped with a grabber, capable of picking up a token which is in front of the robot and within 0.4 metres of the robot's centre. To pick up a token, call the `R.grab` method:

```python
success = R.grab()
```

The `R.grab` function returns `True` if a token was successfully picked up, or `False` otherwise. If the robot is already holding a token, it will throw an `AlreadyHoldingSomethingException`.

To drop the token, call the `R.release` method.

Cable-tie flails are not implemented.


[sr-api]: https://studentrobotics.org/docs/programming/sr/
