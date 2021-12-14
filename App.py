import dearpygui.dearpygui as dpg
import os
from Waypoints import Waypoints
from modules import *
from modules.CaveBot import CaveBot
from modules.Healing import Healing
from modules.Utils import Utils
import asyncio
from modules.AttackSpells import AttackSpells
import sys

# Create Objects
healing = Healing()
utils = Utils()
cavebot = CaveBot()
attack_spells = AttackSpells()
# Values
waypoints_list = os.listdir('./data')
name = None
should_run = True
should_heal = None
should_eat = None
should_walk = None
should_attackspells = None
courutines = []


def cave_bot_set(Value):
    """ Selects waypoints """
    global name, should_walk
    name = dpg.get_value(Value)
    should_walk = name
    update_item(name)

    points_obj = Waypoints(name)
    name = points_obj.select_json()

    return name


def healing_start(Value):
    """ Starts healing """
    global should_heal
    should_heal = dpg.get_value(Value)
    return should_heal


def eating_start(Value):
    """ Starts eating """
    global should_eat
    should_eat = dpg.get_value(Value)
    return dpg.get_value(Value)


def spells_start(Value):
    """ Starts spell attacks """
    global should_attackspells
    should_attackspells = dpg.get_value(Value)
    return dpg.get_value(Value)


def start_or_stop(Value):
    state = dpg.get_value(Value)
    print(state)
    global should_run
    print(should_run)
    asyncio.run(start_coroutines()) if should_run else sys.exit() 
    # if state else stop_coroutines()
def window():
    """ Configures window and viewport"""
    VIEWPORT_WIDTH = 250
    VIEWPORT_HEIGHT = 160
    with dpg.window(label="MyWindow",
                width=400,
                height=270,
                no_move=True,
                no_close=True
                ) as main_window:
        dpg.add_text("Select script from the list:")
        # dpg.add_checkbox(label="Set Up", callback=check)
        dpg.add_separator()
        # dpg.add_checkbox(label="Hunting", callback=core.killandwalk)
        dpg.add_listbox(label="Waypoints", items=waypoints_list, callback=cave_bot_set)
        dpg.add_text(label='Running script: ',default_value='None',id=1)
        dpg.add_separator()

        dpg.add_checkbox(label="Healing", callback=healing_start)

        dpg.add_checkbox(label="Eating", callback=eating_start)

        dpg.add_checkbox(label="Attack Spells", callback=spells_start)
        dpg.add_spacing(count=5)
        dpg.add_button(label='Run', width=45, height=45, callback=start_or_stop)

    dpg.setup_viewport()
    dpg.set_primary_window(main_window, True)
    dpg.configure_viewport(
        title='Notepad',
        item=0,
        height=VIEWPORT_HEIGHT,
        width=VIEWPORT_WIDTH,
        pos=[400, 400],
        always_on_top=True

    )


def update_item(item):
    """ Updates label with a currently running script """
    dpg.configure_item(1, default_value = item)



def main():
    window()
    dpg.start_dearpygui()


async def start_coroutines():
    print(should_heal)
    courutines.append(healing.primary_healing()) if should_heal else None
    courutines.append(utils.auto_eat()) if should_eat else None
    courutines.append(cavebot.run_cvb(name)) if should_walk else None
    courutines.append(attack_spells.run_spells()) if should_attackspells else None
    global should_run
    should_run = False
    print(*courutines)
    await asyncio.gather(
        *courutines
    )


def stop_coroutines():
    tasks =  asyncio.all_tasks()
    print(tasks)
    for t in tasks:
        t.cancel()

if __name__ == "__main__":
    main()
