import random

from core.Supervisor import FEATURE_REQUIREMENTS
from detection.Components import ComponentType
from detection.Readers import battle_entries


class AttackSpellsFeature:
    """ Casts single-target spells on a targeted monster, or area spells when enough monsters are listed """
    key = 'attack_spells'
    label = 'Attack spells'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            battle = battle_entries(ctx.capture(ComponentType.BATTLE_LIST), ctx.layout.scale)
            if not battle.targeted:
                await ctx.sleep(0.05)
                continue
            spells = ctx.settings.attack_spells
            hotkeys = ctx.settings.hotkeys
            if battle.count >= spells.aoe_min_monsters:
                keys = (hotkeys.spell_aoe, hotkeys.spell_aoe_strong)
            else:
                keys = (hotkeys.spell_single, hotkeys.spell_single_2)
            for key in keys:
                await ctx.press(key)
            await ctx.sleep(random.uniform(spells.cooldown_min_s, spells.cooldown_max_s))
