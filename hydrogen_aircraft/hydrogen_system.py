from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
from math import pi


class HydrogenTank(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Hydrogen Tank

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines a simple cylindrical tank with circular caps. Future changes could allow different
    cap shapes, but the current design is sufficient for this analysis.
    """

    # Inputs
    tank_outer_diameter = Input(validator=Positive())
    tank_cylindrical_length = Input()

    @tank_cylindrical_length.validator
    def tank_cylindrical_length(self, value):
        if value < 0:
            from tkinter import Tk, messagebox
            Tk().withdraw()
            messagebox.showwarning('Warning: Invalid Tank',
                                   'The hydrogen tanks are no longer valid. Please reverse the '
                                   'last change, reduce the number of tanks or increase the '
                                   'available tank space by reducing the number of passengers.')
            self.color = 'red'
        else:
            self.color= 'yellow'
        return value > 0

    # Parts
    @Part
    def tank_cylindrical_section(self):
        return Cylinder(radius=self.tank_outer_diameter / 2,
                        height=self.tank_cylindrical_length,
                        position=rotate(translate(self.position,
                                                  'x', self.tank_outer_diameter / 2),
                                        'y', 90, deg=True))

    @Part
    def fwd_tank_cap(self):
        return Sphere(radius=self.tank_outer_diameter / 2,
                      angle=pi,
                      position=rotate(translate(self.position,
                                                'x', self.tank_outer_diameter / 2),
                                      'z', 90, deg=True))

    @Part
    def aft_tank_cap(self):
        return Sphere(radius=self.tank_outer_diameter / 2,
                      angle=pi,
                      position=rotate(translate(self.position,
                                                'x', self.tank_cylindrical_length +
                                                self.tank_outer_diameter / 2),
                                      'z', -90, deg=True))

    @Attribute
    def tank_volume(self):
        return self.tank_cylindrical_section.volume + self.fwd_tank_cap.volume + \
               self.aft_tank_cap.volume


if __name__ == '__main__':
    from parapy.gui import display
    obj = HydrogenTank(tank_outer_diameter=3.4, tank_cylindrical_length=5)
    display(obj)
