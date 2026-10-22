import random

from core.Supervisor import FEATURE_REQUIREMENTS
from detection.Components import ComponentType
from detection.Readers import chase_state, hunger_present


# How often to look for the hunger icon when eating only when hungry
HUNGER_CHECK_S = 5.0


class EatingFeature:
    """ Presses the food hotkey on a random interval, or only while the hunger icon shows """
    key = 'eating'
    label = 'Eating'

    def requires(self, settings):
        if settings.eating.when_hungry:
            return frozenset({ComponentType.STATUS_ICONS})
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            eating = ctx.settings.eating
            if eating.when_hungry:
                hungry = hunger_present(ctx.capture(ComponentType.STATUS_ICONS), ctx.template('hunger.png'))
                if not hungry:
                    await ctx.sleep(min(HUNGER_CHECK_S, eating.interval_min_s))
                    continue
            await ctx.press(ctx.settings.hotkeys.food)
            await ctx.sleep(round(random.uniform(eating.interval_min_s, eating.interval_max_s), 2))


class ChaseFeature:
    """ Turns chase mode on whenever it is off """
    key = 'chase'
    label = 'Auto chase'

    def requires(self, settings):
        return FEATURE_REQUIREMENTS[self.key]

    async def run(self, ctx):
        while True:
            await ctx.ready()
            image = ctx.capture(ComponentType.COMBAT_CONTROLS)
            state = chase_state(image, ctx.template('chase_on.png'), ctx.template('chase_off.png'))
            if state is None:
                ctx.report_mismatch(ComponentType.COMBAT_CONTROLS, 'chase button not recognised')
            elif not state:
                await ctx.press(ctx.settings.hotkeys.chase)
            await ctx.sleep(round(random.uniform(1.05, 1.75), 2))
