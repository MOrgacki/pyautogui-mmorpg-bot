import asyncio
import time
from unittest import TestCase

from config.Settings import Settings
from core.Supervisor import FeatureState, Supervisor
from detection.Components import ComponentType
from tests.fakes import FakeCapture, FakeDetector, FakeInput, make_layout, official_api


def wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class LoopFeature:
    """ Presses a key on every pass once ready """

    def __init__(self, key='healing', requires=frozenset(), press=None):
        self.key = key
        self.label = key.title()
        self._requires = frozenset(requires)
        self._press = press
        self.passes = 0
        self.seen_settings = []

    def requires(self, settings):
        return self._requires

    async def run(self, ctx):
        while True:
            await ctx.ready()
            self.passes += 1
            self.seen_settings.append(ctx.settings)
            if self._press:
                await ctx.press(self._press)
            await asyncio.sleep(0.01)


class FailingFeature(LoopFeature):

    async def run(self, ctx):
        await ctx.ready()
        raise RuntimeError('boom')


class SupervisorTestCase(TestCase):

    def setUp(self):
        self.api, self.window = official_api()
        self.input = FakeInput()
        self.detector = FakeDetector()
        self.supervisor = Supervisor(
            Settings(), window_api=self.api, capture=FakeCapture(), game_input=self.input,
            detector=self.detector, client_poll_s=0.05,
            monitor_options={'poll_s': 0.02, 'settle_s': 0.05, 'periodic_s': 0.2})

    def tearDown(self):
        self.supervisor.shutdown()

    def start(self, *features):
        for feature in features:
            self.supervisor.register(feature)
        self.supervisor.start()
        self.assertTrue(wait_until(lambda: self.supervisor.snapshot.selected_hwnd == 1))
        self.assertTrue(wait_until(lambda: self.supervisor.snapshot.layout is not None))

    def state(self, key):
        status = next(f for f in self.supervisor.snapshot.features if f.key == key)
        return status.state, status.pause_reason

    def log_messages(self, source):
        return [e.message for e in self.supervisor.log.entries(500, source)]


class TestSupervisorLifecycle(SupervisorTestCase):

    def test_start_runs_feature_on_bot_thread(self):
        feature = LoopFeature()
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: feature.passes > 3))
        self.assertEqual(self.state('healing'), (FeatureState.RUNNING, None))

    def test_stop_feature_within_one_second(self):
        healing, eating = LoopFeature('healing'), LoopFeature('eating')
        self.start(healing, eating)
        self.supervisor.start_feature('healing').result(1)
        self.supervisor.start_feature('eating').result(1)
        self.assertTrue(wait_until(lambda: eating.passes > 0))
        started = time.monotonic()
        self.supervisor.stop_feature('eating').result(1)
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(self.state('eating')[0], FeatureState.OFF)
        passes = healing.passes
        self.assertTrue(wait_until(lambda: healing.passes > passes))

    def test_stop_all_within_one_second(self):
        features = [LoopFeature('healing'), LoopFeature('eating')]
        self.start(*features)
        for feature in features:
            self.supervisor.start_feature(feature.key).result(1)
        started = time.monotonic()
        self.supervisor.stop_all().result(1)
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual({f.state for f in self.supervisor.snapshot.features}, {FeatureState.OFF})
        self.assertFalse(self.supervisor.snapshot.running)

    def test_start_all_starts_only_enabled(self):
        healing, eating = LoopFeature('healing'), LoopFeature('eating')
        self.supervisor._settings = Settings().with_feature_enabled('eating', True)
        self.start(healing, eating)
        self.supervisor.start_all().result(1)
        self.assertTrue(wait_until(lambda: eating.passes > 0))
        self.assertEqual(healing.passes, 0)
        self.assertEqual(self.state('healing')[0], FeatureState.OFF)

    def test_error_turns_feature_off_and_is_logged(self):
        self.start(FailingFeature())
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: any('boom' in m for m in self.log_messages('healing'))))
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.OFF))
        errors = [e for e in self.supervisor.log.entries(500, 'healing') if e.level == 'error']
        self.assertEqual(len(errors), 1)

    def test_apply_settings_seen_on_next_pass(self):
        feature = LoopFeature()
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        new = Settings().with_group('healing', low_hp_percent=20)
        self.supervisor.apply_settings(new).result(1)
        self.assertTrue(wait_until(lambda: feature.seen_settings and feature.seen_settings[-1] == new))


class TestSupervisorPausing(SupervisorTestCase):

    def test_pauses_while_component_missing_and_sends_nothing(self):
        self.detector.layout_factory = lambda hwnd, generation: make_layout(
            hwnd, found=set(ComponentType) - {ComponentType.HEALTH_BAR}, generation=generation)
        feature = LoopFeature(requires={ComponentType.HEALTH_BAR}, press='f8')
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: self.state('healing') == (FeatureState.PAUSED, 'health bar not found')))
        time.sleep(0.2)
        self.assertEqual(self.input.presses, [])
        self.assertEqual(feature.passes, 0)

    def test_resumes_when_component_returns(self):
        missing = {'value': True}
        self.detector.layout_factory = lambda hwnd, generation: make_layout(
            hwnd, found=set() if missing['value'] else None, generation=generation)
        feature = LoopFeature(requires={ComponentType.HEALTH_BAR}, press='f8')
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.PAUSED))
        missing['value'] = False
        self.supervisor.detect_now().result(1)
        started = time.monotonic()
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.RUNNING, 1.0))
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertTrue(wait_until(lambda: 'f8' in self.input.presses))

    def test_periodic_retry_finds_returning_component(self):
        missing = {'value': True}
        self.detector.layout_factory = lambda hwnd, generation: make_layout(
            hwnd, found=set() if missing['value'] else None, generation=generation)
        feature = LoopFeature(requires={ComponentType.HEALTH_BAR})
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.PAUSED))
        missing['value'] = False
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.RUNNING, 1.5))

    def test_not_focused_pauses(self):
        feature = LoopFeature(press='f8')
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: feature.passes > 0))
        self.api.foreground_hwnd = None
        self.assertTrue(wait_until(lambda: self.state('healing') == (FeatureState.PAUSED, 'client not focused')))
        count = len(self.input.presses)
        time.sleep(0.2)
        self.assertEqual(len(self.input.presses), count)

    def test_minimized_or_lost_pauses_everything(self):
        features = [LoopFeature('healing'), LoopFeature('eating')]
        self.start(*features)
        for feature in features:
            self.supervisor.start_feature(feature.key).result(1)
        self.window.minimized = True
        self.assertTrue(wait_until(lambda: all(
            self.state(k) == (FeatureState.PAUSED, 'client minimized') for k in ('healing', 'eating'))))
        self.assertTrue(wait_until(lambda: self.supervisor.snapshot.client_state == 'minimized'))
        self.window.minimized = False
        self.window.exists = False
        self.assertTrue(wait_until(lambda: all(
            self.state(k) == (FeatureState.PAUSED, 'client lost') for k in ('healing', 'eating'))))

    def test_recheck_failure_marks_component_missing(self):
        feature = LoopFeature(requires={ComponentType.BATTLE_LIST})
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.RUNNING))
        self.detector.failing = {ComponentType.BATTLE_LIST}
        self.detector.layout_factory = lambda hwnd, generation: make_layout(
            hwnd, found=set(ComponentType) - {ComponentType.BATTLE_LIST}, generation=generation)
        self.assertTrue(wait_until(lambda: self.state('healing') == (FeatureState.PAUSED, 'battle list not found')))


class TestSupervisorLog(SupervisorTestCase):

    def test_events_are_logged_with_sources(self):
        missing = {'value': True}
        self.detector.layout_factory = lambda hwnd, generation: make_layout(
            hwnd, found=set() if missing['value'] else None, generation=generation)
        feature = LoopFeature(requires={ComponentType.HEALTH_BAR})
        self.start(feature)
        self.supervisor.start_feature('healing').result(1)
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.PAUSED))
        missing['value'] = False
        self.supervisor.detect_now().result(1)
        self.assertTrue(wait_until(lambda: self.state('healing')[0] is FeatureState.RUNNING))
        self.supervisor.stop_feature('healing').result(1)

        healing = self.log_messages('healing')
        self.assertIn('Started', healing)
        self.assertIn('Paused: health bar not found', healing)
        self.assertIn('Resumed', healing)
        self.assertIn('Stopped', healing)
        detection = self.log_messages('detection')
        self.assertTrue(any(m == 'health bar missing: anchor not found' for m in detection))
        self.assertTrue(any(m == 'health bar found' for m in detection))
        self.assertTrue(any(m.startswith('Selected client') for m in self.log_messages('supervisor')))
        paused = next(e for e in self.supervisor.log.entries(500, 'healing') if e.message.startswith('Paused'))
        self.assertEqual(paused.level, 'warning')

    def test_log_keeps_newest_500(self):
        log = self.supervisor.log
        for i in range(600):
            log.add('test', f"entry {i}")
        self.assertEqual(len(log), 500)
        self.assertEqual(log.entries(1)[0].message, 'entry 599')
