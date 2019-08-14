from __future__ import division

import threading


class GameObject(object):
    surface_name = None
    marker_id = None
    grabbable = False
    grabbed = False

    def __init__(self, arena):
        self.arena = arena

        self._location = (0, 0)
        self._heading = 0

        self.lock = threading.RLock()

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, val):
        self._location = val

    @property
    def heading(self):
        return self._heading

    @location.setter
    def location(self,val):
        self._heading = val
