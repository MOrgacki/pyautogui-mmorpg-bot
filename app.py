import dearpygui.dearpygui as dpg
from modules import core
from multiprocessing import freeze_support
import jsonMaker
import os
from modules import healing

VIEWPORT_WIDTH = 360
VIEWPORT_HEIGHT = 120

waypoints_list = os.listdir('./data')


def main():
    freeze_support()
    dpg.start_dearpygui()


def waypoint(Sender):
    '''
    Starts a hunt
    '''
    name = dpg.get_value(Sender)
    lista = jsonMaker.select_json(name)
    core.killandwalk(lista)


# def chase(task):
    '''
    Executes chasing through checkbox
    '''
#     if dpg.get_value(task) == True:
#         print(dpg.get_value(task))
#         core.chase()


with dpg.window(label="Fluffies 😌",
                width=200,
                height=60,
                no_move=True,
                no_close=True
                ) as main_window:
    dpg.add_text("OrganBot")
    # dpg.add_checkbox(label="Set Up", callback=check)
    dpg.add_same_line()
    # dpg.add_checkbox(label="Hunting", callback=core.killandwalk)
    dpg.add_listbox(label="Waypoints", items=waypoints_list, callback=waypoint)
    dpg.add_same_line()
    dpg.add_checkbox(label="Chase", callback=core.chase)
    dpg.add_same_line()
    dpg.add_checkbox(label="heal", callback=healing.heal)

dpg.setup_viewport()
dpg.set_primary_window(main_window, True)
dpg.configure_viewport(
    title='Fluffies 😌',
    item=0,
    height=VIEWPORT_HEIGHT,
    width=VIEWPORT_WIDTH,
    pos=[400, 400],
    always_on_top=True

)


if __name__ == "__main__":
    main()
