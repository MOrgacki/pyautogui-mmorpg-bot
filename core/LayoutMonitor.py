import asyncio
import time

from core.ClientWindow import WindowState


class LayoutMonitor:
    """ Watches the selected client and asks for detection when its window or layout changes (research R10) """

    def __init__(self, get_window, detect, periodic, poll_s=0.25, settle_s=0.3, periodic_s=2.0):
        self._get_window = get_window
        self._detect = detect
        self._periodic = periodic
        self._poll_s = poll_s
        self._settle_s = settle_s
        self._periodic_s = periodic_s
        self._requested = None

    def request_detection(self, reason):
        """ Full detection on the next pass (keeps the first reason if several arrive) """
        self._requested = self._requested or reason

    async def run(self):
        last_hwnd = None
        last_rect = None
        last_state = None
        changed_at = None
        last_check = time.monotonic()

        while True:
            window = self._get_window()
            if window is None:
                last_hwnd = last_rect = last_state = changed_at = None
                await asyncio.sleep(self._poll_s)
                continue

            window.refresh()
            now = time.monotonic()
            if window.hwnd != last_hwnd:
                last_hwnd, last_rect, changed_at = window.hwnd, None, None
                self.request_detection('client selected')

            if window.state is WindowState.VISIBLE:
                if last_state is WindowState.MINIMIZED:
                    self.request_detection('client restored')
                elif last_rect is not None and window.client_rect != last_rect:
                    # Wait for the move or resize to settle before detecting
                    changed_at = now
                last_rect = window.client_rect
            last_state = window.state

            if changed_at is not None and now - changed_at >= self._settle_s:
                changed_at = None
                self.request_detection('window moved or resized')

            if window.state is WindowState.VISIBLE and changed_at is None:
                if self._requested is not None:
                    reason, self._requested = self._requested, None
                    await self._detect(reason)
                    last_check = time.monotonic()
                elif now - last_check >= self._periodic_s:
                    await self._periodic()
                    last_check = time.monotonic()

            await asyncio.sleep(self._poll_s)
