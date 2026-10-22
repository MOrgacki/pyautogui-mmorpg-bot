from unittest import IsolatedAsyncioTestCase

import numpy as np

from config.Settings import Settings
from detection.Components import ComponentType
from modules.Utils import ChaseFeature, EatingFeature
from tests.fakes import FakeContext, run_feature
from tests.synthetic import make_templates


C = ComponentType


class TestEating(IsolatedAsyncioTestCase):

    async def test_eats_on_interval(self):
        ctx = FakeContext(max_passes=3)
        await run_feature(EatingFeature(), ctx)
        self.assertEqual(ctx.presses, ['f5', 'f5', 'f5'])
        for delay in ctx.sleeps:
            self.assertTrue(20.3 <= delay <= 30.7)

    async def test_when_hungry_only_eats_with_icon(self):
        hunger = make_templates()['hunger.png']
        strip = np.full((12, 100, 3), 60, np.uint8)
        hungry = strip.copy()
        hungry[1:11, 40:50] = hunger
        settings = Settings().with_group('eating', when_hungry=True)
        ctx = FakeContext(settings=settings, images={C.STATUS_ICONS: [strip, hungry]},
                          templates={'hunger.png': hunger}, max_passes=2)
        await run_feature(EatingFeature(), ctx)
        self.assertEqual(ctx.presses, ['f5'])
        self.assertEqual(ctx.sleeps[0], 5.0)

    def test_requires_depends_on_mode(self):
        self.assertEqual(EatingFeature().requires(Settings()), frozenset())
        self.assertEqual(EatingFeature().requires(Settings().with_group('eating', when_hungry=True)),
                         {C.STATUS_ICONS})


class TestChase(IsolatedAsyncioTestCase):

    def context(self, showing):
        images = make_templates()
        return FakeContext(images={C.COMBAT_CONTROLS: images[showing]},
                           templates={'chase_on.png': images['chase_on.png'],
                                      'chase_off.png': images['chase_off.png']})

    async def test_turns_chase_on(self):
        ctx = self.context('chase_off.png')
        await run_feature(ChaseFeature(), ctx)
        self.assertEqual(ctx.presses, ['f12'])
        self.assertTrue(1.05 <= ctx.sleeps[0] <= 1.75)

    async def test_leaves_chase_on(self):
        ctx = self.context('chase_on.png')
        await run_feature(ChaseFeature(), ctx)
        self.assertEqual(ctx.presses, [])
        self.assertEqual(len(ctx.sleeps), 1)
