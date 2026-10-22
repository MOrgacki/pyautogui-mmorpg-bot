""" Stand-ins for Win32, screen capture, input and detection so tests never touch the real screen """
import numpy as np

from detection.Components import ComponentType, DetectedComponent, Layout, Region


OFFICIAL_EXE = r'C:\Users\Player\AppData\Local\Tibia\packages\Tibia\bin\client.exe'


class FakeWindow:
    def __init__(self, hwnd, title, exe, rect=Region(100, 50, 800, 600), visible=True, minimized=False):
        self.hwnd = hwnd
        self.title = title
        self.exe = exe
        self.rect = rect
        self.visible = visible
        self.minimized = minimized
        self.exists = True


class FakeWindowApi:
    def __init__(self, windows=(), foreground=None):
        self.windows = {w.hwnd: w for w in windows}
        self.foreground_hwnd = foreground

    def enum_windows(self):
        return [h for h, w in self.windows.items() if w.exists]

    def exists(self, hwnd):
        return hwnd in self.windows and self.windows[hwnd].exists

    def title(self, hwnd):
        return self.windows[hwnd].title

    def is_visible(self, hwnd):
        return self.windows[hwnd].visible

    def is_minimized(self, hwnd):
        return self.windows[hwnd].minimized

    def pid(self, hwnd):
        return hwnd + 1000

    def exe(self, pid):
        return self.windows[pid - 1000].exe

    def client_rect(self, hwnd):
        return None if self.windows[hwnd].minimized else self.windows[hwnd].rect

    def foreground(self):
        return self.foreground_hwnd


def official_api(hwnd=1, title='Tibia - Knight', focused=True):
    """ A fake desktop with one official client """
    window = FakeWindow(hwnd, title, OFFICIAL_EXE)
    return FakeWindowApi([window], foreground=hwnd if focused else None), window


class FakeCapture:
    def __init__(self, image=None):
        self.image = image if image is not None else np.zeros((600, 800, 3), np.uint8)
        self.region_images = {}

    def capture_client(self, window):
        return self.image

    def capture_region(self, window, region):
        if region in self.region_images:
            return self.region_images[region]
        return region.crop(self.image)

    def close(self):
        pass


class FakeInput:
    """ Records input; refuses it when the window is not focused, like GameInput """

    def __init__(self):
        self.presses = []
        self.clicks = []

    async def press_async(self, window, key):
        if window is None or not window.refresh().is_foreground:
            return False
        self.presses.append(key)
        return True

    async def click_async(self, window, client_point, button='left', modifier=None):
        if window is None or not window.refresh().is_foreground:
            return False
        self.clicks.append((client_point, button, modifier))
        return True


def make_layout(hwnd=1, found=None, regions=None, generation=1, detail=None):
    """ Layout where the given types are found (default: all) """
    found = set(ComponentType) if found is None else set(found)
    regions = regions or {}
    detail = detail or {}
    components = {}
    for component_type in ComponentType:
        if component_type in found:
            region = regions.get(component_type, Region(10, 10, 100, 20))
            components[component_type] = DetectedComponent(
                component_type, True, region, 0.99, 1.0, detail.get(component_type, {}))
        else:
            components[component_type] = DetectedComponent.missing(component_type, 'anchor not found')
    return Layout(hwnd, (800, 600), components, 1.0, 0.0, generation)


class FakeDetector:
    """ Returns whatever layout the test sets; counts calls """

    def __init__(self, layout_factory=None):
        self.layout_factory = layout_factory or (lambda hwnd, generation: make_layout(hwnd, generation=generation))
        self.detect_calls = 0
        self.recheck_calls = 0
        self.failing = set()

    def detect(self, image, hwnd, generation):
        self.detect_calls += 1
        return self.layout_factory(hwnd, generation)

    def recheck(self, image, layout):
        self.recheck_calls += 1
        return set(self.failing)


class FakeContext:
    """ FeatureContext stand-in. ready() raises CancelledError after max_passes, ending the feature like Stop """

    def __init__(self, layout=None, settings=None, images=None, templates=None, marks=None,
                 running=(), max_passes=1):
        from config.Settings import Settings
        self.layout = layout or make_layout()
        self.settings = settings or Settings()
        self.images = images or {}
        self.templates = templates or {}
        self.marks = marks or {}
        self.running = set(running)
        self.max_passes = max_passes
        self.passes = 0
        self.presses = []
        self.clicks = []
        self.sleeps = []
        self.waits = []
        self.mismatches = []
        self.logs = []

    async def ready(self):
        import asyncio
        if self.passes >= self.max_passes:
            raise asyncio.CancelledError()
        self.passes += 1

    async def sleep(self, seconds):
        self.sleeps.append(seconds)

    async def wait(self, reason, seconds=0.5):
        self.waits.append(reason)

    def capture(self, component):
        """ images[component] is an image, or a list of images returned in turn (the last one repeats) """
        image = self.images[component]
        if isinstance(image, list):
            return image.pop(0) if len(image) > 1 else image[0]
        return image

    def template(self, name):
        return self.templates[name]

    def mark(self, path):
        return self.marks[path]

    async def press(self, key):
        self.presses.append(key)
        return True

    async def click(self, client_point, button='left', modifier=None):
        self.clicks.append((client_point, button, modifier))
        return True

    def report_mismatch(self, component, reason):
        self.mismatches.append(component)

    def log(self, message, level='info'):
        self.logs.append((level, message))

    def is_running(self, key):
        return key in self.running


async def run_feature(feature, ctx):
    """ Runs a feature until FakeContext stops it """
    import asyncio
    try:
        await feature.run(ctx)
    except asyncio.CancelledError:
        pass
