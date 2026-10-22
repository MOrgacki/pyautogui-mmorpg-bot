import ntpath
from dataclasses import dataclass
from enum import Enum

from config.DetectionConfig import DetectionConfig
from detection.Components import Region


class WindowState(Enum):
    VISIBLE = 'visible'
    MINIMIZED = 'minimized'
    LOST = 'lost'


class Win32Api:
    """ The Win32 calls the bot needs. Tests pass a fake with the same methods """

    def enum_windows(self):
        import win32gui
        handles = []
        win32gui.EnumWindows(lambda hwnd, _: handles.append(hwnd) or True, None)
        return handles

    def exists(self, hwnd):
        import win32gui
        return bool(win32gui.IsWindow(hwnd))

    def title(self, hwnd):
        import win32gui
        return win32gui.GetWindowText(hwnd)

    def is_visible(self, hwnd):
        import win32gui
        return bool(win32gui.IsWindowVisible(hwnd))

    def is_minimized(self, hwnd):
        import win32gui
        return bool(win32gui.IsIconic(hwnd))

    def pid(self, hwnd):
        import win32process
        return win32process.GetWindowThreadProcessId(hwnd)[1]

    def exe(self, pid):
        import psutil
        try:
            return psutil.Process(pid).exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return ''

    def client_rect(self, hwnd):
        """ Client area in screen coordinates, or None when it has no size """
        import win32gui
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        if right - left <= 0 or bottom - top <= 0:
            return None
        x, y = win32gui.ClientToScreen(hwnd, (left, top))
        return Region(x, y, right - left, bottom - top)

    def foreground(self):
        import win32gui
        return win32gui.GetForegroundWindow()


@dataclass
class ClientWindow:
    """ One running official Tibia client """
    hwnd: int
    title: str
    pid: int
    exe_path: str
    client_rect: Region | None
    state: WindowState
    is_foreground: bool
    api: object = None

    def refresh(self):
        """ Re-reads title, rectangle, state and focus. Returns self """
        api = self.api
        if not api.exists(self.hwnd):
            self.state = WindowState.LOST
            self.is_foreground = False
            return self
        self.title = api.title(self.hwnd)
        if api.is_minimized(self.hwnd):
            self.state = WindowState.MINIMIZED
        else:
            self.state = WindowState.VISIBLE
            self.client_rect = api.client_rect(self.hwnd) or self.client_rect
        self.is_foreground = api.foreground() == self.hwnd
        return self

    def to_screen(self, point):
        """ Client point -> screen point """
        if self.client_rect is None:
            raise ValueError('client window has no known position')
        return (self.client_rect.x + point[0], self.client_rect.y + point[1])

    @property
    def size(self):
        return (self.client_rect.width, self.client_rect.height) if self.client_rect else (0, 0)


def is_official_client(title, exe_path, config):
    if not title.startswith(config.title_prefix):
        return False
    exe_name = ntpath.basename(exe_path).lower()
    return exe_name == config.client_exe_name.lower() and config.client_path_marker in exe_path.lower()


def find_client_windows(config=None, api=None):
    """ Lists visible windows of the official client, ordered by title """
    config = config or DetectionConfig()
    api = api or Win32Api()
    clients = []
    for hwnd in api.enum_windows():
        if not api.is_visible(hwnd):
            continue
        title = api.title(hwnd)
        if not title.startswith(config.title_prefix):
            continue
        pid = api.pid(hwnd)
        exe_path = api.exe(pid)
        if not is_official_client(title, exe_path, config):
            continue
        minimized = api.is_minimized(hwnd)
        clients.append(ClientWindow(
            hwnd=hwnd,
            title=title,
            pid=pid,
            exe_path=exe_path,
            client_rect=None if minimized else api.client_rect(hwnd),
            state=WindowState.MINIMIZED if minimized else WindowState.VISIBLE,
            is_foreground=api.foreground() == hwnd,
            api=api,
        ))
    return sorted(clients, key=lambda c: c.title)
