from core.Supervisor import FEATURE_REQUIREMENTS
from detection.Components import ComponentType
from detection.Readers import bar_percent


PASS_DELAY_S = 0.05


class HealingFeature:
    """ Heals with the low or high heal hotkey when health drops below the thresholds """
    key = 'healing'
    label = 'Healing'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            await self.step(ctx)
            await ctx.sleep(PASS_DELAY_S)

    async def step(self, ctx):
        health = bar_percent(ctx.capture(ComponentType.HEALTH_BAR))
        if health <= 0:
            # A living character never shows an empty bar; the region is probably wrong
            ctx.report_mismatch(ComponentType.HEALTH_BAR, 'health bar reads empty')
            return
        settings = ctx.settings
        if health >= settings.healing.high_hp_percent:
            return
        if self._mana_refill_first(ctx):
            return
        if health < settings.healing.low_hp_percent:
            await ctx.press(settings.hotkeys.heal_low)
        else:
            await ctx.press(settings.hotkeys.heal_high)

    def _mana_refill_first(self, ctx):
        """ A heal needs mana: while mana refill runs and mana is low, let it refill first """
        if not ctx.is_running('mana_refill') or not ctx.layout.has(ComponentType.MANA_BAR):
            return False
        mana = bar_percent(ctx.capture(ComponentType.MANA_BAR))
        return mana < ctx.settings.mana.refill_below_percent


class ManaRefillFeature:
    """ Presses the mana hotkey when mana drops below the threshold """
    key = 'mana_refill'
    label = 'Mana refill'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            mana = bar_percent(ctx.capture(ComponentType.MANA_BAR))
            if mana < ctx.settings.mana.refill_below_percent:
                await ctx.press(ctx.settings.hotkeys.mana)
            await ctx.sleep(PASS_DELAY_S)
