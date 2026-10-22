import asyncio
from unittest import IsolatedAsyncioTestCase

from core.ClientWindow import find_client_windows
from core.LayoutMonitor import LayoutMonitor
from detection.Components import Region
from tests.fakes import official_api


class TestLayoutMonitor(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.api, self.fake = official_api()
        self.window = find_client_windows(api=self.api)[0]
        self.detections = []
        self.periodic_calls = 0

        async def detect(reason):
            self.detections.append(reason)

        async def periodic():
            self.periodic_calls += 1

        self.monitor = LayoutMonitor(lambda: self.window, detect, periodic,
                                     poll_s=0.01, settle_s=0.1, periodic_s=0.15)
        self.task = asyncio.create_task(self.monitor.run())

    async def asyncTearDown(self):
        self.task.cancel()
        await asyncio.gather(self.task, return_exceptions=True)

    async def test_detects_on_selection(self):
        await asyncio.sleep(0.05)
        self.assertEqual(self.detections, ['client selected'])

    async def test_one_detection_after_resize_settles(self):
        await asyncio.sleep(0.05)
        for width in (900, 1000, 1100, 1200, 1300):
            self.fake.rect = Region(0, 0, width, 700)
            await asyncio.sleep(0.03)
        self.assertEqual(self.detections, ['client selected'])
        await asyncio.sleep(0.2)
        self.assertEqual(self.detections, ['client selected', 'window moved or resized'])

    async def test_minimized_then_restored(self):
        await asyncio.sleep(0.05)
        self.fake.minimized = True
        await asyncio.sleep(0.3)
        self.assertEqual(self.detections, ['client selected'])
        calls = self.periodic_calls
        await asyncio.sleep(0.2)
        self.assertEqual(self.periodic_calls, calls)
        self.fake.minimized = False
        await asyncio.sleep(0.05)
        self.assertEqual(self.detections, ['client selected', 'client restored'])

    async def test_mismatch_request(self):
        await asyncio.sleep(0.05)
        self.monitor.request_detection('health bar mismatch')
        await asyncio.sleep(0.05)
        self.assertEqual(self.detections[-1], 'health bar mismatch')

    async def test_periodic_check(self):
        await asyncio.sleep(0.4)
        self.assertGreaterEqual(self.periodic_calls, 2)
