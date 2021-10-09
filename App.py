import dearpygui.dearpygui as dpg
import os
from Waypoints import Waypoints
from modules import *
from modules.CaveBot import CaveBot
from modules.Healing import Healing

# Create Objects
cavebot = CaveBot()
healing = Healing()

waypoints_list = os.listdir('./data')

"""Starts a bot"""
def cave_bot_start(Value):
    name = dpg.get_value(Value)
    waypts = Waypoints(name)
    name = waypts.select_json(name)
    cavebot.start(selected_name=name)

"""Starts a healing"""
def healing_start(Value):
    if dpg.get_value(Value) == True:
        # waypts = Waypoints(name)
        # name = waypts.select_json(name)
        # # core.killandwalk(lista)
        healing.primary_healing()

def window():
    VIEWPORT_WIDTH = 360
    VIEWPORT_HEIGHT = 120
    with dpg.window(label="MyWindow",
                width=400,
                height=160,
                no_move=True,
                no_close=True
                ) as main_window:
        dpg.add_text("Select waypoints from list:")
        # dpg.add_checkbox(label="Set Up", callback=check)
        dpg.add_separator()
        # dpg.add_checkbox(label="Hunting", callback=core.killandwalk)
        dpg.add_listbox(label="Waypoints", items=waypoints_list, callback=cave_bot_start)
        dpg.add_separator()
        dpg.add_same_line()
        dpg.add_checkbox(label="Healing", callback=healing_start)

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

def main():
    window()
    dpg.start_dearpygui()



if __name__ == "__main__":
    main()
