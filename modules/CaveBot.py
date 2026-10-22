import random
import time

from Waypoints import Waypoints
from core.Supervisor import FEATURE_REQUIREMENTS
from detection.Components import ComponentType
from detection.Readers import battle_entries, find_mark, is_arrived, loot_message_present


C = ComponentType

# The 9 tiles around and under the character, as tile offsets from it
LOOT_TILES = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
# Click the waypoint mark again if the character has not arrived after this long
RECLICK_S = 3.0


class AttackFeature:
    """ Attacks an untargeted monster from the battle list and waits until it is no longer targeted """
    key = 'attack'
    label = 'Attack monsters'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            battle = battle_entries(ctx.capture(C.BATTLE_LIST), ctx.layout.scale)
            if battle.count > 0 and not battle.targeted:
                ctx.log('Monster detected, attacking')
                await ctx.press(ctx.settings.hotkeys.attack)
                await self._wait_while_targeted(ctx)
            await ctx.sleep(0.05)

    async def _wait_while_targeted(self, ctx):
        while True:
            await ctx.ready()
            if not battle_entries(ctx.capture(C.BATTLE_LIST), ctx.layout.scale).targeted:
                return
            await ctx.sleep(0.05)


class LootFeature:
    """ After a kill, if the chat shows a loot message, shift+right-clicks the tiles around the character """
    key = 'loot'
    label = 'Loot'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        was_targeted = False
        while True:
            await ctx.ready()
            targeted = battle_entries(ctx.capture(C.BATTLE_LIST), ctx.layout.scale).targeted
            if was_targeted and not targeted and loot_message_present(ctx.capture(C.CHAT)):
                await self.loot(ctx)
            was_targeted = targeted
            await ctx.sleep(0.05)

    async def loot(self, ctx):
        tiles = list(LOOT_TILES)
        random.shuffle(tiles)
        for dx, dy in tiles:
            # Shift is pressed and released around each click by GameInput
            await ctx.click(ctx.layout.tile_point(dx, dy), button='right', modifier='shift')
        ctx.log('Looted around the character')


class WalkFeature:
    """ Walks the selected route by clicking its marks on the minimap, in order, wrapping to the first """
    key = 'walk'
    label = 'Walk route'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    def __init__(self):
        self.position = 0
        self._route_name = None
        self._marks = []
        self._refreshed_for = None
        self._clicked_at = None

    def _load_route(self, ctx):
        name = ctx.settings.cavebot.route
        if name != self._route_name:
            self._route_name = name
            self._marks = Waypoints(name).select_json() if name else []
            self.position = 0
            self._clicked_at = None
        return self._marks

    async def run(self, ctx):
        while True:
            await ctx.ready()
            marks = self._load_route(ctx)
            if not marks:
                await ctx.wait('no route selected', 1.0)
                continue
            if battle_entries(ctx.capture(C.BATTLE_LIST), ctx.layout.scale).count > 0:
                # Monsters first; attacking is the attack feature's job
                await ctx.sleep(0.1)
                continue
            await self.step(ctx, marks)
            await ctx.sleep(0.1)

    async def step(self, ctx, marks):
        self.position %= len(marks)
        mark_path = marks[self.position]
        minimap = ctx.layout.get(C.MINIMAP).region
        point = find_mark(ctx.capture(C.MINIMAP), ctx.mark(mark_path))
        if point is None:
            if self._refreshed_for != self.position:
                # Recovery: the mark may be off the visible map; refresh it once per mark
                self._refreshed_for = self.position
                await ctx.press(ctx.settings.hotkeys.refresh_map)
                ctx.log(f"Mark {mark_path} not found on the minimap; refreshed the map", 'warning')
            return
        self._refreshed_for = None
        if is_arrived(point, (minimap.width, minimap.height), ctx.settings.cavebot.arrival_radius_percent):
            ctx.log(f"Reached {mark_path}")
            self.position = (self.position + 1) % len(marks)
            self._clicked_at = None
            return
        now = time.monotonic()
        if self._clicked_at is None or now - self._clicked_at >= RECLICK_S:
            await ctx.click((minimap.x + point[0], minimap.y + point[1]))
            self._clicked_at = now
