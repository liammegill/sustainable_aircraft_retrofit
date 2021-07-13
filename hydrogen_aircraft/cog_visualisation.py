from parapy.geom import *
from parapy.core import *


class COGVisualisation(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: COGVisualisation

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Tuesday 27th April 2021

    Defines a the center of gravity visualization. The sphere represents the x position of the
    center of gravity and the rod represents the mean aerodynamic chord. The visualization is
    meant to give a visual clue to the user of the c.g. position wrt to the MAC.
    """
    mac = Input()
    x_mac = Input()
    mainwing_span = Input()
    aircraft_cog_x = Input()

    @Part
    def mac_rod(self):
        return Box(self.mac, 0.05, 0.05,
                   position=translate(self.position,
                                      'x', self.x_mac,
                                      'y', -(self.mainwing_span / 2) * 1.2))

    @Part
    def cog_x_sphere(self):
        return Sphere(radius=0.2,
                      color=[255, 0, 0],
                      position=translate(self.position,
                                         'x', self.aircraft_cog_x,
                                         'y', -(self.mainwing_span / 2) * 1.2))
