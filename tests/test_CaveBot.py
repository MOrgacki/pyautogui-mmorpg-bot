import ast
from unittest import IsolatedAsyncioTestCase, TestCase

from config.Settings import Settings
from detection.Components import ComponentType, Region
from detection.Readers import loot_message_present
from detection.Templates import read_image
from modules.CaveBot import AttackFeature, LootFeature, WalkFeature
from tests.fakes import FakeContext, make_layout, run_feature
from tests.synthetic import make_battle, make_minimap


C = ComponentType
MINIMAP = Region(600, 100, 106, 109)
GAME_VIEW = Region(0, 0, 480, 352)


class TestLootFixtures(TestCase):
    """ The original loot tests, now through the loot reader """

    def test_for_loot(self):
        self.assertTrue(loot_message_present(read_image('tests/testdata/loot_found.png')))

    def test_for_no_loot(self):
        self.assertFalse(loot_message_present(read_image('tests/testdata/empty_loot.png')))


class TestAttack(IsolatedAsyncioTestCase):

    async def test_attacks_untargeted_monster_and_waits(self):
        battle = [make_battle(1), make_battle(1, True), make_battle(1, True), make_battle(0)]
        ctx = FakeContext(images={C.BATTLE_LIST: battle}, max_passes=4)
        await run_feature(AttackFeature(), ctx)
        self.assertEqual(ctx.presses, ['f1'])

    async def test_no_monsters(self):
        ctx = FakeContext(images={C.BATTLE_LIST: make_battle(0)})
        await run_feature(AttackFeature(), ctx)
        self.assertEqual(ctx.presses, [])


class TestLoot(IsolatedAsyncioTestCase):

    def context(self, chat, passes=2):
        layout = make_layout(regions={C.GAME_VIEW: GAME_VIEW}, detail={C.GAME_VIEW: {'tile_size': 32}})
        return FakeContext(layout=layout, max_passes=passes, images={
            C.BATTLE_LIST: [make_battle(1, True), make_battle(0)],
            C.CHAT: read_image(chat),
        })

    async def test_loots_nine_tiles_after_kill(self):
        ctx = self.context('tests/testdata/loot_found.png')
        await run_feature(LootFeature(), ctx)
        points = {point for point, _, _ in ctx.clicks}
        expected = {ctx.layout.tile_point(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        self.assertEqual(points, expected)
        self.assertEqual({(button, modifier) for _, button, modifier in ctx.clicks}, {('right', 'shift')})

    async def test_no_loot_message(self):
        ctx = self.context('tests/testdata/empty_loot.png')
        await run_feature(LootFeature(), ctx)
        self.assertEqual(ctx.clicks, [])

    async def test_no_kill_no_loot(self):
        layout = make_layout()
        ctx = FakeContext(layout=layout, max_passes=3, images={
            C.BATTLE_LIST: make_battle(0), C.CHAT: read_image('tests/testdata/loot_found.png')})
        await run_feature(LootFeature(), ctx)
        self.assertEqual(ctx.clicks, [])


class TestWalk(IsolatedAsyncioTestCase):

    def setUp(self):
        self.marks = {path: read_image(path) for path in (
            'images/marks/bagmark.png', 'images/marks/blueflagmark.png', 'images/marks/questionmark.png')}

    def context(self, minimaps, passes, battle=None):
        settings = Settings().with_group('cavebot', route='3points.json')
        layout = make_layout(regions={C.MINIMAP: MINIMAP})
        return FakeContext(layout=layout, settings=settings, marks=self.marks, max_passes=passes, images={
            C.MINIMAP: minimaps, C.BATTLE_LIST: battle if battle is not None else make_battle(0)})

    async def test_clicks_mark_and_advances_on_arrival(self):
        bag = self.marks['images/marks/bagmark.png']
        flag = self.marks['images/marks/blueflagmark.png']
        minimaps = [make_minimap(bag, at=(20, 30)), make_minimap(bag, at=(53, 54)), make_minimap(flag, at=(90, 80))]
        feature = WalkFeature()
        ctx = self.context(minimaps, 3)
        await run_feature(feature, ctx)
        clicked = [point for point, _, _ in ctx.clicks]
        self.assertEqual(len(clicked), 2)
        self.assertLessEqual(abs(clicked[0][0] - (600 + 20)), 1)
        self.assertLessEqual(abs(clicked[0][1] - (100 + 30)), 1)
        self.assertLessEqual(abs(clicked[1][0] - (600 + 90)), 1)
        self.assertEqual(feature.position, 1)

    async def test_wraps_to_first_mark(self):
        feature = WalkFeature()
        arrived = [make_minimap(m, at=(53, 54)) for m in self.marks.values()]
        ctx = self.context(arrived, 3)
        await run_feature(feature, ctx)
        self.assertEqual(feature.position, 0)
        self.assertEqual(ctx.clicks, [])

    async def test_mark_not_found_refreshes_map_once(self):
        empty = make_minimap(None)
        ctx = self.context([empty], 3)
        await run_feature(WalkFeature(), ctx)
        self.assertEqual(ctx.presses, ['f6'])
        self.assertTrue(any('not found' in message for level, message in ctx.logs if level == 'warning'))

    async def test_waits_for_monsters(self):
        bag = self.marks['images/marks/bagmark.png']
        ctx = self.context([make_minimap(bag, at=(20, 30))], 2, battle=make_battle(1))
        await run_feature(WalkFeature(), ctx)
        self.assertEqual(ctx.clicks, [])

    async def test_no_route_pauses(self):
        ctx = FakeContext(max_passes=1)
        await run_feature(WalkFeature(), ctx)
        self.assertEqual(ctx.waits, ['no route selected'])


class TestNoBareExcept(TestCase):

    def test_cavebot_has_no_bare_except(self):
        with open('modules/CaveBot.py', encoding='utf-8') as file:
            tree = ast.parse(file.read())
        bare = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and n.type is None]
        self.assertEqual(bare, [])
