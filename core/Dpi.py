import ctypes


PER_MONITOR_DPI_AWARE = 2


def make_dpi_aware():
    """ Makes window rects, captures and clicks all use physical pixels (research R3).
    Must run before pyautogui, mss or dearpygui are imported. """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PER_MONITOR_DPI_AWARE)
    except (AttributeError, OSError):
        # Windows versions without shcore
        ctypes.windll.user32.SetProcessDPIAware()
