from parapy.core import Input, Part, child
from parapy.geom import GeomBase, Box, translate, rotate
from parapy.core.validate import GreaterThan, is_string


class Seat(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Seat

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines simplified seats for use in an aircraft. Can be used for passenger seats (
    type='pax'), cabin crew seats (type='crew') and pilot seats (type='pilot'). The number of
    seats in a block is given by n_seats. The class defaults to economy class seating found
    standard in an Airbus A320.

    All quantities in metres.
    """

    # Inputs
    n_seats = Input(3, private=not (__name__ == '__main__'), validator=GreaterThan(0))
    type = Input('pax', validator=is_string)

    seat_width = Input(0.43, private=not (__name__ == '__main__'), validator=GreaterThan(0))
    seat_height = Input(1.1, validator=GreaterThan(0))
    seat_depth = Input(0.5, private=not (__name__ == '__main__'), validator=GreaterThan(0))

    back_cushion_thickness = Input(0.07, validator=GreaterThan(0))
    seat_cushion_thickness = Input(0.1, validator=GreaterThan(0))
    chair_leg_height = Input(0.35, validator=GreaterThan(0))
    chair_leg_width = Input(0.03, validator=GreaterThan(0))

    armrest_width = Input(0.05, private=not (__name__ == '__main__'), validator=GreaterThan(0))
    armrest_height_ground = Input(0.60, validator=GreaterThan(0))

    @Part(in_tree=False)
    def simple_seat_volume(self):
        return Box(self.seat_depth,
                   self.n_seats * self.seat_width + self.armrest_width,
                   self.seat_height,
                   transparency=0.5,
                   color='red')

    @Part
    def seat_cushion(self):
        """Horizontal part of chair"""
        return Box(self.seat_depth * 0.8,
                   self.n_seats * self.seat_width,
                   self.seat_cushion_thickness,
                   position=translate(self.position,
                                      'y', 0.5 * self.armrest_width,
                                      'z', self.chair_leg_height))

    @Part
    def seat_back(self):
        """Back of chair, at an angle of 10 deg for illustration. Suppressed for type='crew'"""
        return Box(self.back_cushion_thickness,
                   self.seat_width - self.armrest_width,
                   self.seat_height - self.chair_leg_height - self.seat_cushion_thickness,
                   quantify=self.n_seats,
                   position=rotate(translate(self.position,
                                             'x', self.seat_depth * 0.8 -
                                             self.back_cushion_thickness,
                                             'y', self.armrest_width + child.index *
                                             self.seat_width,
                                             'z', self.chair_leg_height +
                                             self.seat_cushion_thickness),
                                   'y', 10, deg=True),
                   suppress=self.type == 'crew')

    @Part
    def armrests(self):
        """Simple armrests. Suppressed for type='pilot' and type='crew'"""
        return Box(self.seat_depth * 0.6,
                   self.armrest_width,
                   self.armrest_width,
                   quantify=self.n_seats + 1,
                   position=translate(self.position,
                                      'x', 0.2 * self.seat_depth,
                                      'y', child.index * self.seat_width,
                                      'z', self.armrest_height_ground),
                   suppress=self.type == 'pilot' or self.type == 'crew')

    @Part
    def fwd_chair_leg(self):
        """Simple front chair leg. Suppressed for type='crew'"""
        return Box(self.chair_leg_width,
                   self.chair_leg_width,
                   self.chair_leg_height,
                   quantify=self.n_seats + 1,
                   position=translate(self.position,
                                      'y', 0.5 * self.armrest_width +
                                      child.index * ((self.n_seats * self.seat_width -
                                                      self.chair_leg_width) / self.n_seats)),
                   suppress=self.type == 'crew')

    @Part
    def aft_chair_leg(self):
        """Simple back chair leg. Suppressed for type='crew'"""
        return Box(self.chair_leg_width,
                   self.chair_leg_width,
                   self.chair_leg_height,
                   quantify=self.n_seats + 1,
                   position=translate(self.position,
                                      'y', 0.5 * self.armrest_width +
                                      child.index * ((self.n_seats * self.seat_width -
                                                      self.chair_leg_width) / self.n_seats),
                                      'x', self.seat_depth * 0.8 - self.chair_leg_width),
                   suppress=self.type == 'crew')


if __name__ == '__main__':
    from parapy.gui import display

    obj = Seat(type='pilot')
    display(obj)
