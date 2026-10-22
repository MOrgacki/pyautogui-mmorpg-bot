import numpy as np


class ScreenCapture:
    """ Captures the client window, or part of it, as BGR numpy arrays """

    def __init__(self):
        # Created on first use, on the thread that captures (mss handles are per thread)
        self._mss = None

    def _grabber(self):
        if self._mss is None:
            import mss
            self._mss = mss.MSS()
        return self._mss

    def grab(self, screen_region):
        """ Captures a screen-coordinate Region """
        shot = self._grabber().grab({
            'left': screen_region.x,
            'top': screen_region.y,
            'width': screen_region.width,
            'height': screen_region.height,
        })
        # BGRA -> BGR
        return np.asarray(shot)[:, :, :3].copy()

    def capture_client(self, window):
        if window.client_rect is None:
            raise ValueError('client window has no known position')
        return self.grab(window.client_rect)

    def capture_region(self, window, region):
        """ Captures a client-coordinate Region of the window """
        x, y = window.to_screen((region.x, region.y))
        return self.grab(region.offset(x - region.x, y - region.y))

    def close(self):
        if self._mss is not None:
            self._mss.close()
            self._mss = None
