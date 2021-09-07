import dearpygui.dearpygui as dpg
from pebble.common import stop_process
import pebble
from modules import core
import config as cfg

VIEWPORT_WIDTH = 400
VIEWPORT_HEIGHT = 60

'''
Executes Test task with process stop logic implemented
'''


def check(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        test = core.setUp()
        result = pebble.ProcessFuture.result(self=test)

    else:
        stop_process(task)


'''
Executes hunting through checkbox
'''


def hunt(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        core.killandwalk()


'''
Executes chasing through checkbox
'''


def chase(task):
    if dpg.get_value(task) == True:
        print(dpg.get_value(task))
        core.chase()


with dpg.window(label="Fluffies 😌",
                width=200,
                height=60,
                no_move=True,
                no_close=True
                ) as main_window:
    dpg.add_text("Let journey begins - created by Marcin Orgacki")
    dpg.add_checkbox(label="Set Up", callback=check)
    dpg.add_same_line()
    dpg.add_checkbox(label="Hunting", callback=core.killandwalk)
    dpg.add_same_line()
    dpg.add_checkbox(label="Chase", callback=core.chase)
    dpg.add_same_line()
    dpg.add_checkbox(label="heal", callback=core.heal)

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
