import asyncio
import concurrent.futures
import threading
import time
from dataclasses import dataclass, replace
from enum import Enum
from typing import Protocol

from config.DetectionConfig import DetectionConfig
from core.ActivityLog import ActivityLog
from core.ClientWindow import Win32Api, WindowState, find_client_windows
from core.GameInput import GameInput
from core.ScreenCapture import ScreenCapture
from detection.Components import ComponentType, DetectedComponent, Layout


C = ComponentType

# Components each feature needs before it may act (data-model.md)
FEATURE_REQUIREMENTS = {
    'healing': frozenset({C.HEALTH_BAR}),
    'mana_refill': frozenset({C.MANA_BAR}),
    'eating': frozenset(),
    'attack_spells': frozenset({C.BATTLE_LIST}),
    'chase': frozenset({C.COMBAT_CONTROLS}),
    'attack': frozenset({C.BATTLE_LIST}),
    # Loot also reads the battle list: a kill is the target frame disappearing
    'loot': frozenset({C.CHAT, C.GAME_VIEW, C.BATTLE_LIST}),
    'walk': frozenset({C.MINIMAP, C.BATTLE_LIST}),
}


class Feature(Protocol):
    key: str
    label: str

    def requires(self, settings) -> frozenset: ...

    async def run(self, ctx) -> None: ...


class FeatureState(Enum):
    OFF = 'off'
    RUNNING = 'running'
    PAUSED = 'paused'


@dataclass(frozen=True)
class FeatureStatus:
    key: str
    label: str
    state: FeatureState = FeatureState.OFF
    pause_reason: str | None = None


@dataclass(frozen=True)
class ClientInfo:
    hwnd: int
    title: str


@dataclass(frozen=True)
class StatusSnapshot:
    """ Read-only view of the bot for the UI. Replaced whole, never edited """
    clients: tuple = ()
    selected_hwnd: int | None = None
    client_state: str = 'none'
    layout: Layout | None = None
    capture: object = None
    detection_seconds: float | None = None
    features: tuple = ()
    running: bool = False


class FeatureContext:
    """ What a feature may use. See contracts/feature-interface.md """

    def __init__(self, supervisor, feature):
        self._supervisor = supervisor
        self._feature = feature

    @property
    def layout(self):
        return self._supervisor._layout

    @property
    def settings(self):
        return self._supervisor._settings

    def is_running(self, key):
        """ True when another feature is currently running (not paused or off) """
        return self._supervisor._statuses[key].state is FeatureState.RUNNING

    async def ready(self):
        """ Returns once the feature may act; pauses it with a reason until then """
        supervisor = self._supervisor
        key = self._feature.key
        while True:
            reason = supervisor._block_reason(self._feature)
            if reason is None:
                supervisor._set_state(key, FeatureState.RUNNING)
                return
            supervisor._set_state(key, FeatureState.PAUSED, reason)
            await supervisor._wait_for_change(0.5)

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)

    async def wait(self, reason, seconds=0.5):
        """ Pauses the feature for a reason of its own (e.g. no route selected) """
        self._supervisor._set_state(self._feature.key, FeatureState.PAUSED, reason)
        await asyncio.sleep(seconds)

    def capture(self, component):
        region = self.layout.get(component).region
        return self._supervisor._capture.capture_region(self._supervisor._window, region)

    def template(self, name):
        """ An inner or anchor template at the current UI scale """
        return self._supervisor._ensure_detector().templates.get(name, self.layout.scale)

    def mark(self, path):
        """ A waypoint mark image at the current UI scale """
        return self._supervisor._ensure_detector().templates.load_mark(path, self.layout.scale)

    async def press(self, key):
        sent = await self._supervisor._input.press_async(self._supervisor._window, key)
        if not sent:
            self._supervisor._set_state(self._feature.key, FeatureState.PAUSED, 'client not focused')
        return sent

    async def click(self, client_point, button='left', modifier=None):
        sent = await self._supervisor._input.click_async(self._supervisor._window, client_point, button, modifier)
        if not sent:
            self._supervisor._set_state(self._feature.key, FeatureState.PAUSED, 'client not focused')
        return sent

    def report_mismatch(self, component, reason):
        self.log(f"{component.value} looks wrong ({reason}); re-detecting", 'warning')
        self._supervisor.request_detection(f"{component.value} mismatch")

    def log(self, message, level='info'):
        self._supervisor.log.add(self._feature.key, message, level)


class Supervisor:
    """ Runs the bot's asyncio loop on one worker thread; the UI talks to it through the public methods """

    def __init__(self, settings, log=None, config=None, window_api=None, capture=None,
                 game_input=None, detector=None, client_poll_s=1.0, monitor_options=None):
        self.log = log or ActivityLog()
        self._settings = settings
        self._config = config or DetectionConfig()
        self._api = window_api or Win32Api()
        self._capture = capture or ScreenCapture()
        self._input = game_input or GameInput()
        self._detector = detector
        self._client_poll_s = client_poll_s
        self._monitor_options = monitor_options or {}

        self._features = {}
        self._contexts = {}
        self._statuses = {}
        self._tasks = {}
        self._clients = ()
        self._window = None
        self._layout = None
        self._last_capture = None
        self._detection_seconds = None
        self._generation = 0

        self._lock = threading.Lock()
        self._snapshot = StatusSnapshot()
        self._loop = None
        self._thread = None
        self._change_event = None
        self._detect_lock = None
        self._monitor = None
        self._detector_error = None

    # ----- lifecycle -----

    def start(self):
        """ Starts the worker thread and its event loop """
        ready = threading.Event()

        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._change_event = asyncio.Event()
            self._detect_lock = asyncio.Lock()
            self._loop.create_task(self._watch_clients())
            self._loop.create_task(self._run_monitor())
            ready.set()
            self._loop.run_forever()
            self._loop.close()

        self._thread = threading.Thread(target=run, name='bot-loop', daemon=True)
        self._thread.start()
        ready.wait()

    def shutdown(self, timeout=2.0):
        """ Stops every feature, then the loop. Waits up to timeout seconds """
        if self._loop is None:
            return
        try:
            self.stop_all().result(timeout)
        except concurrent.futures.TimeoutError:
            self.log.add('supervisor', 'Features did not stop in time', 'warning')
        try:
            self._submit(self._cancel_background()).result(timeout)
        except concurrent.futures.TimeoutError:
            self.log.add('supervisor', 'Background tasks did not stop in time', 'warning')
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout)

    async def _cancel_background(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # Capture handles belong to the thread that created them: close them here, on the bot thread
        self._capture.close()

    # ----- thread-safe API (returns concurrent futures) -----

    @property
    def snapshot(self):
        with self._lock:
            return self._snapshot

    @property
    def settings(self):
        return self._settings

    def register(self, feature):
        """ Adds a feature; call before start() """
        self._features[feature.key] = feature
        self._contexts[feature.key] = FeatureContext(self, feature)
        self._statuses[feature.key] = FeatureStatus(feature.key, feature.label)
        self._publish()

    def requirements(self, key):
        return self._features[key].requires(self._settings)

    def select_client(self, hwnd):
        return self._submit(self._select_client(hwnd))

    def start_feature(self, key):
        return self._submit(self._start_feature(key))

    def stop_feature(self, key):
        return self._submit(self._stop_features([key]))

    def start_all(self):
        return self._submit(self._start_all())

    def stop_all(self):
        return self._submit(self._stop_features(list(self._tasks)))

    def apply_settings(self, settings):
        return self._submit(self._apply_settings(settings))

    def detect_now(self):
        return self._submit(self._detect('requested by user'))

    def request_detection(self, reason):
        """ Asks the layout monitor for a full detection on its next pass """
        if self._monitor is not None:
            self._loop.call_soon_threadsafe(self._monitor.request_detection, reason)

    def _submit(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    # ----- loop-thread internals -----

    async def _select_client(self, hwnd):
        match = [c for c in find_client_windows(self._config, self._api) if c.hwnd == hwnd]
        if not match:
            self.log.add('supervisor', f"Client window {hwnd} not found", 'warning')
            return
        if self._window is not None and self._window.hwnd == hwnd:
            return
        self._window = match[0]
        self._layout = None
        self.log.add('supervisor', f"Selected client '{self._window.title}'")
        self._notify_change()
        self.request_detection('client selected')

    async def _start_feature(self, key):
        task = self._tasks.get(key)
        if task is not None and not task.done():
            return
        self._set_state(key, FeatureState.PAUSED, 'starting')
        self.log.add(key, 'Started')
        self._tasks[key] = asyncio.get_running_loop().create_task(self._run_feature(self._features[key]))

    async def _start_all(self):
        for key in self._features:
            if self._settings.features.enabled.get(key):
                await self._start_feature(key)

    async def _stop_features(self, keys):
        tasks = [self._tasks.pop(k) for k in keys if k in self._tasks]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=1.0)

    async def _apply_settings(self, settings):
        self._settings = settings
        self._notify_change()

    async def _run_feature(self, feature):
        key = feature.key
        try:
            await feature.run(self._contexts[key])
            self.log.add(key, 'Finished')
        except asyncio.CancelledError:
            self.log.add(key, 'Stopped')
            raise
        except Exception as error:
            # The supervisor boundary: an unexpected error ends only this feature (contract rule 7)
            self.log.add(key, f"Stopped after an error: {error!r}", 'error')
        finally:
            if self._tasks.get(key) is asyncio.current_task():
                del self._tasks[key]
            self._set_state(key, FeatureState.OFF)

    def _block_reason(self, feature):
        window = self._window
        if window is None:
            return 'no client selected'
        window.refresh()
        if window.state is WindowState.LOST:
            return 'client lost'
        if window.state is WindowState.MINIMIZED:
            return 'client minimized'
        if not window.is_foreground:
            return 'client not focused'
        requires = feature.requires(self._settings)
        if not requires:
            return None
        layout = self._layout
        if layout is None or layout.window_hwnd != window.hwnd:
            return 'waiting for detection'
        missing = layout.missing(*sorted(requires, key=lambda t: t.value))
        if missing:
            return f"{missing[0].value} not found"
        return None

    def _set_state(self, key, state, reason=None):
        old = self._statuses[key]
        if old.state is state and old.pause_reason == reason:
            return
        self._statuses[key] = replace(old, state=state, pause_reason=reason)
        if state is FeatureState.PAUSED and reason != 'starting':
            self.log.add(key, f"Paused: {reason}", 'warning')
        elif state is FeatureState.RUNNING and old.state is FeatureState.PAUSED and old.pause_reason != 'starting':
            self.log.add(key, 'Resumed')
        self._publish()

    async def _wait_for_change(self, timeout):
        event = self._change_event
        try:
            await asyncio.wait_for(event.wait(), timeout)
        except TimeoutError:
            pass

    def _notify_change(self):
        """ Wakes paused features so they re-check right away """
        if self._change_event is not None:
            self._change_event.set()
            self._change_event = asyncio.Event()
        self._publish()

    def _client_state(self):
        window = self._window
        if window is None:
            return 'none'
        if window.state is WindowState.LOST:
            return 'lost'
        if window.state is WindowState.MINIMIZED:
            return 'minimized'
        return 'found' if window.is_foreground else 'not focused'

    def _publish(self):
        snapshot = StatusSnapshot(
            clients=tuple(ClientInfo(c.hwnd, c.title) for c in self._clients),
            selected_hwnd=self._window.hwnd if self._window else None,
            client_state=self._client_state(),
            layout=self._layout,
            capture=self._last_capture,
            detection_seconds=self._detection_seconds,
            features=tuple(self._statuses[k] for k in self._features),
            running=any(not t.done() for t in self._tasks.values()),
        )
        with self._lock:
            self._snapshot = snapshot

    # ----- clients -----

    async def _watch_clients(self):
        while True:
            self._clients = tuple(find_client_windows(self._config, self._api))
            if self._window is not None:
                self._window.refresh()
            self._auto_select()
            self._publish()
            await asyncio.sleep(self._client_poll_s)

    def _auto_select(self):
        selected = self._window
        if selected is not None and selected.state is not WindowState.LOST:
            return
        candidates = list(self._clients)
        if selected is not None:
            candidates = [c for c in candidates if c.hwnd != selected.hwnd]
        last_title = self._settings.client.last_title
        chosen = None
        if len(candidates) == 1:
            chosen = candidates[0]
        elif last_title:
            chosen = next((c for c in candidates if c.title == last_title), None)
        if chosen is not None:
            self._loop.create_task(self._select_client(chosen.hwnd))

    # ----- detection -----

    def _ensure_detector(self):
        """ Builds the template detector on first use; logs and returns None if templates are missing """
        if self._detector is None:
            from detection.LayoutDetector import TemplateDetector
            try:
                self._detector = TemplateDetector(self._config)
            except FileNotFoundError as error:
                message = f"Detection templates missing: {error}"
                # Retried on every detection; log only when the problem changes
                if message != self._detector_error:
                    self._detector_error = message
                    self.log.add('detection', message, 'error')
                return None
        return self._detector

    async def _run_monitor(self):
        from core.LayoutMonitor import LayoutMonitor
        self._monitor = LayoutMonitor(
            get_window=lambda: self._window,
            detect=self._detect,
            periodic=self._periodic_check,
            **self._monitor_options,
        )
        await self._monitor.run()

    async def _capture_visible_client(self):
        window = self._window
        if window is None:
            return None, None
        window.refresh()
        if window.state is not WindowState.VISIBLE:
            return window, None
        return window, self._capture.capture_client(window)

    async def _detect(self, reason):
        """ Full detection of the selected client """
        async with self._detect_lock:
            window, image = await self._capture_visible_client()
            if image is None:
                return
            detector = self._ensure_detector()
            self._generation += 1
            started = time.perf_counter()
            if detector is None:
                layout = Layout.empty(window.hwnd, window.size, 'detection templates missing',
                                      self._generation, time.monotonic())
            else:
                layout = await asyncio.get_running_loop().run_in_executor(
                    None, detector.detect, image, window.hwnd, self._generation)
            self._detection_seconds = time.perf_counter() - started
            self._last_capture = image
            if reason != 'periodic retry':
                self.log.add('detection', f"Detected layout ({reason}) in {self._detection_seconds:.2f} s")
            self._set_layout(layout)

    async def _periodic_check(self):
        """ Re-detects while something is missing, otherwise re-checks the known anchors """
        layout = self._layout
        if layout is None or not all(c.found for c in layout.components.values()):
            await self._detect('periodic retry')
            return
        detector = self._ensure_detector()
        if detector is None:
            return
        async with self._detect_lock:
            window, image = await self._capture_visible_client()
            if image is None or layout is not self._layout:
                return
            failing = await asyncio.get_running_loop().run_in_executor(None, detector.recheck, image, layout)
        if failing:
            components = dict(layout.components)
            for component_type in failing:
                components[component_type] = DetectedComponent.missing(component_type, 'component stopped matching')
            self._generation += 1
            self._set_layout(replace(layout, components=components, generation=self._generation))

    def _set_layout(self, layout):
        old = self._layout
        for component_type, component in layout.components.items():
            was_found = old is not None and old.get(component_type).found
            if component.found and not was_found:
                self.log.add('detection', f"{component_type.value} found")
            elif not component.found and (was_found or old is None):
                self.log.add('detection', f"{component_type.value} missing: {component.missing_reason}", 'warning')
        self._layout = layout
        self._notify_change()
