from unittest import IsolatedAsyncioTestCase

from config.Settings import Settings
from detection.Components import ComponentType
from modules.Healing import HealingFeature, ManaRefillFeature
from tests.fakes import FakeContext, run_feature
from tests.synthetic import make_bar


C = ComponentType


class TestHealing(IsolatedAsyncioTestCase):

    async def heal(self, health, mana=100, running=(), settings=None, passes=1):
        ctx = FakeContext(images={C.HEALTH_BAR: make_bar(health), C.MANA_BAR: make_bar(mana)},
                          running=running, settings=settings, max_passes=passes)
        await run_feature(HealingFeature(), ctx)
        return ctx

    async def test_low_health_uses_low_heal(self):
        self.assertEqual((await self.heal(30)).presses, ['f4'])

    async def test_medium_health_uses_high_heal(self):
        self.assertEqual((await self.heal(70)).presses, ['f8'])

    async def test_full_health_does_nothing(self):
        self.assertEqual((await self.heal(95)).presses, [])

    async def test_mana_refill_goes_first_while_it_runs(self):
        self.assertEqual((await self.heal(30, mana=20, running={'mana_refill'})).presses, [])

    async def test_heals_regardless_of_mana_when_refill_is_off(self):
        self.assertEqual((await self.heal(30, mana=20)).presses, ['f4'])

    async def test_empty_bar_is_a_mismatch(self):
        ctx = await self.heal(0)
        self.assertEqual(ctx.presses, [])
        self.assertEqual(ctx.mismatches, [C.HEALTH_BAR])

    async def test_uses_current_settings_every_pass(self):
        ctx = FakeContext(images={C.HEALTH_BAR: make_bar(70)}, max_passes=2)

        feature = HealingFeature()
        await run_feature(feature, ctx)
        self.assertEqual(ctx.presses, ['f8', 'f8'])
        ctx.settings = Settings().with_group('hotkeys', heal_high='f9')
        ctx.max_passes = 3
        await run_feature(feature, ctx)
        self.assertEqual(ctx.presses[-1], 'f9')

    async def test_every_pass_awaits(self):
        ctx = await self.heal(95, passes=3)
        self.assertEqual(len(ctx.sleeps), 3)


class TestManaRefill(IsolatedAsyncioTestCase):

    async def refill(self, mana):
        ctx = FakeContext(images={C.MANA_BAR: make_bar(mana, colour=(200, 80, 0))})
        await run_feature(ManaRefillFeature(), ctx)
        return ctx

    async def test_low_mana(self):
        self.assertEqual((await self.refill(40)).presses, ['f7'])

    async def test_enough_mana(self):
        self.assertEqual((await self.refill(80)).presses, [])

    def test_requires(self):
        self.assertEqual(ManaRefillFeature().requires(Settings()), {C.MANA_BAR})
        self.assertEqual(HealingFeature().requires(Settings()), {C.HEALTH_BAR})
