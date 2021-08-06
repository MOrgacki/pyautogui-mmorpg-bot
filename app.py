import dearpygui.dearpygui as dpg
from pebble.common import stop_process
import pebble
import coreFunctions

VIEWPORT_WIDTH = 400
VIEWPORT_HEIGHT = 60


def check(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        test = coreFunctions.setUp()
        result = pebble.ProcessFuture.result(self=test)

    else:
        stop_process(task)


def hunt(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        coreFunctions.killandwalk()


def chase(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        coreFunctions.chase()


with dpg.window(label="Fluffies 😌",
                width=200,
                height=60,
                no_move=True,
                no_close=True
                ) as main_window:
    dpg.add_text("Let journey begins - created by Marcin Orgacki")
    dpg.add_checkbox(label="Set Up", callback=check)
    dpg.add_same_line()
    dpg.add_checkbox(label="Hunting", callback=coreFunctions.killandwalk)
    dpg.add_same_line()
    dpg.add_checkbox(label="Chase", callback=coreFunctions.chase)
    dpg.add_same_line()
    dpg.add_checkbox(label="heal")

dpg.setup_viewport()
dpg.set_primary_window(main_window, True)
dpg.configure_viewport(
    title='Fluffies 😌',
    item=0,
    height=VIEWPORT_HEIGHT,
    width=VIEWPORT_WIDTH,
    pos=[200, 200],
    always_on_top=True

)
if __name__ == "__main__":
    dpg.start_dearpygui()
