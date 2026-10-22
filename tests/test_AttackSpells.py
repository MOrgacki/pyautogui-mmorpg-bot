from unittest import IsolatedAsyncioTestCase

from detection.Components import ComponentType
from modules.AttackSpells import AttackSpellsFeature
from tests.fakes import FakeContext, run_feature
from tests.synthetic import make_battle


class TestAttackSpells(IsolatedAsyncioTestCase):

    async def cast(self, count, targeted):
        ctx = FakeContext(images={ComponentType.BATTLE_LIST: make_battle(count, targeted)})
        await run_feature(AttackSpellsFeature(), ctx)
        return ctx

    async def test_single_target(self):
        ctx = await self.cast(2, True)
        self.assertEqual(ctx.presses, ['f2', 'f3'])
        self.assertTrue(2.3 <= ctx.sleeps[0] <= 2.8)

    async def test_area_spells(self):
        self.assertEqual((await self.cast(3, True)).presses, ['del', 'end'])

    async def test_nothing_without_target(self):
        ctx = await self.cast(3, False)
        self.assertEqual(ctx.presses, [])
        self.assertEqual(ctx.sleeps, [0.05])
