# Hydrogen Aircraft Retrofit
# KBE Competition Entry at YesDelft, July 15th 2021

# from parapy.lib.webgui import display
# from tkinter import Tk, messagebox
# from hydrogen_aircraft import Aircraft
# from parapy.lib.webgui import display
# from parapy.lib.webgui.components import (
#     Config, Dropdown, Group, Inspector, Numfield, Radiobuttons, Sequence,
#     Slider, Tab, Tree, Viewer, Wizard)
#
# # TODO: open previous save
#
# # load Aircraft with input.txt as obj
# input_file_path = "input.txt"
# obj = Aircraft()
#
# with open(input_file_path) as f:
#     i = 0
#     for line in f:
#         if i > 3:
#             (key, val) = line.split()
#             exec('obj.' + str(key) + '=' + str(val))
#         i += 1
#
# # display obj in webGUI
#
# config = Config(
#     title="Hydrogen Retrofitted Airbus A320",
#     default_visibility=["."],
#     tools=[Tree(position="left", stacked=True),
#            Viewer(position="middle"),
#            Viewer(position="left", default_perspective="front", can_rotate=False, auto_fit=True),
#            Wizard(position="right",
#                   widgets=[
#                       Tab("General", children=[
#                           Slider("n_firstclass_rows", label="First Class Rows",
#                                  min=0, max=10, step=1),
#                           Slider("n_economy_rows", label="Economy Rows",
#                                  min=0, max=20, step=1),
#                           Slider("n_passengers", label="Total Passengers", read_only=True),
#                           Radiobuttons("fuselage.n_hydrogen_tanks", label="hydrogen tanks",
#                                        values=[1,2], labels=["1", "2"])
#                       ]),
#                       Tab("Flight Parameters", children=[
#                           Slider("cruise_mach_number", label='Cruise Mach Number',
#                                  min=0.68, max=0.8, step=0.01),
#                           Slider("cruise_altitude", label="Cruise Altitude [m]",
#                                  min=10000, max=13000)])
#
#                   ])]
# )
#
# display(obj, config, model_name="A320_H2_retrofit")

from parapy.core.snapshot import read_snapshot
from parapy.gui import display
from tkinter import Tk, messagebox
from tkinter.filedialog import askopenfilename
from hydrogen_aircraft import Aircraft

# Ask user whether they want to open a previous save
Tk().withdraw()
user_answer = messagebox.askyesno('Open previous save',
                                  'Welcome to the hydrogen retrofit of a single-aisle '
                                  'aircraft KBE application.\n\nDo you want to open a '
                                  'previous save? If so, note that the input file will '
                                  'ignored.')

# If previous save desired, open json file
if user_answer:
    old_save_path = askopenfilename(title='Open previous save',
                                    filetypes=[('json', '.json')])
    with open(old_save_path) as f:
        obj = read_snapshot(f)

# If no previous save, open Aircraft with input file
else:
    input_file_path = askopenfilename(title='Open input file',
                                      filetypes=[('txt', '.txt')])
    obj = Aircraft()

    # update values with input file values
    with open(input_file_path) as f:
        i = 0
        for line in f:
            if i > 3:  # the input file should have four lines of text that are ignored
                (key, val) = line.split()
                exec('obj.' + str(key) + '=' + str(val))
            i += 1

# Display the Aircraft in GUI
display(obj, autodraw=True)

