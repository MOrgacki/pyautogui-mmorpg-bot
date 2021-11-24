import dearpygui.dearpygui as dpg
import os
from Waypoints import Waypoints
from modules import *
from modules.CaveBot import CaveBot
from modules.Healing import Healing
from modules.Utils import Utils
import asyncio
from modules.AttackSpells import AttackSpells

# Create Objects
healing = Healing()
utils = Utils()
cavebot = CaveBot()
attack_spells = AttackSpells()
# Values
waypoints_list = os.listdir('./data')
name = None

""" Starts a bot """
def cave_bot_start(Value):
    global name
    name = dpg.get_value(Value)
    update_item(name)

    points_obj = Waypoints(name)
    name = points_obj.select_json()
    # cavebot.start(name)

    return name

""" Starts a healing """
def healing_start(Value):

    if dpg.get_value(Value) == True:
         asyncio.run(start())
    elif dpg.get_value(Value) == False:
        healing.stop()

""" Starts eating """
def eating_start(Value):
    if dpg.get_value(Value) == True:
        asyncio.run(start())
    elif dpg.get_value(Value) == False:
        utils.stop()


""" Configures window and viewport"""
def window():
    VIEWPORT_WIDTH = 250
    VIEWPORT_HEIGHT = 100
    with dpg.window(label="MyWindow",
                width=400,
                height=160,
                no_move=True,
                no_close=True
                ) as main_window:
        dpg.add_text("Select script from the list:")
        # dpg.add_checkbox(label="Set Up", callback=check)
        dpg.add_separator()
        # dpg.add_checkbox(label="Hunting", callback=core.killandwalk)
        dpg.add_listbox(label="Waypoints", items=waypoints_list, callback=cave_bot_start)
        dpg.add_text(label='Running script: ',default_value='None',id=1)
        dpg.add_separator()
        dpg.add_same_line()
        dpg.add_checkbox(label="Healing", callback=healing_start)
        dpg.add_same_line()
        dpg.add_checkbox(label="Eating", callback=eating_start)

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

async def start():
    print("start")
    await asyncio.gather(
        healing.primary_healing(),
        utils.auto_eat(),
        cavebot.run_cvb(name),
        # attack_spells.run_spells()

    )

def update_item(item):
    """ Updates label with a currently running script """
    dpg.configure_item(1, default_value = item)




def main():
    window()
    dpg.start_dearpygui()


if __name__ == "__main__":
    main()
