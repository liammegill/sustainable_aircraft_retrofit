from parapy.core import *
from parapy.geom import *
from parapy.core.validate import Positive
import numpy as np


class CargoContainer(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Cargo Container

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines a cargo container. Defaults to an LD3-45 container (symmetric container).
    Un-symmetric containers are not possible to be defined with this class. In future versions,
    a lookup table will be created such that the only input to this class is the name of the
    cargo container.
    """

    # Inputs
    height = Input(1.143, validator=Positive())  # [m]
    width = Input(2.438)  # [m]
    base = Input(1.562, validator=Positive())  # [m]
    depth = Input(1.534, validator=Positive())  # [m]

    @width.validator  # ensure that width is larger than base
    def width(self, value):
        return value > self.base

    # Parts
    # The container is created by subtracting two smaller boxes from a larger one to create the
    # right shape.

    @Part(in_tree=False)
    def container_uncut(self):
        return Box(self.depth, self.width, self.height)

    @Part(in_tree=False)
    def cut_volume_starboard(self):
        return Box(self.depth,
                   np.sqrt(0.5 * (self.width - self.base) ** 2),
                   np.sqrt(0.5 * (self.width - self.base) ** 2),
                   position=rotate(translate(self.position, 'y', 0.5 * (
                       self.width + self.base)), 'x', -45, deg=True))

    @Part(in_tree=False)
    def cut_volume_port(self):
        return Box(self.depth,
                   np.sqrt(0.5 * (self.width - self.base) ** 2),
                   np.sqrt(0.5 * (self.width - self.base) ** 2),
                   position=rotate(translate(self.position, 'y', -0.5 * (
                       self.width - self.base)), 'x', -45, deg=True))

    @Part
    def cargo_container(self):
        return SubtractedSolid(
            shape_in=SubtractedSolid(shape_in=self.container_uncut,
                                     tool=self.cut_volume_starboard),
            tool=self.cut_volume_port)
