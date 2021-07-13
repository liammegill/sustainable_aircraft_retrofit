from parapy.geom import *
from parapy.core import *
from parapy.core.validate import *


class FuselageStructure(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Fuselage Structure

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines the fuselage structure: outer skin of nosecone, tailcone and cylindrical section;
    floors (cabin and cargo); bulkheads.
    """

    # ----- INPUTS ----- #

    # outer geometry variables, passed down from fuselage.py if in main loop
    d_outer = Input(4.14, private=not (__name__ == '__main__'), validator=Positive())
    d_inner = Input(3.94, private=not (__name__ == '__main__'))

    @d_inner.validator  # check that d_inner is less than d_outer
    def d_inner(self, value):
        return value < self.d_outer

    l_fuselage = Input(37.57, private=not (__name__ == '__main__'))
    l_nosecone = Input(5.44, private=not (__name__ == '__main__'), validator=Positive())
    l_tailcone = Input(13.47, private=not (__name__ == '__main__'), validator=Positive())

    @l_fuselage.validator
    def l_fuselage(self, value):
        return value > self.l_nosecone + self.l_tailcone

    @Attribute
    def l_cylindrical(self):
        return self.l_fuselage - self.l_nosecone - self.l_tailcone

    x_cabin_floor_end = Input(14., private=not (__name__ == '__main__'), validator=Positive())

    # nosecone / tailcone for A320. Can be changed once other aircraft are considered
    nosecone_diameters = Input([0.1, 40, 60, 85, 95, 99, 100])
    nosecone_z_translate = Input([-20, -20, -15, -5, -1.5, -0.5, 0], validator=IsInstance(list))
    tailcone_diameters_pos = Input([0, 3, 14, 90, 100], validator=IsInstance(list))
    tailcone_diameters = Input([100, 99.5, 95, 25, 10])
    tailcone_z_translate = Input([0, 0, 2, 22, 25], validator=IsInstance(list))

    # ensure all are within limits
    @nosecone_diameters.validator
    def nosecone_diameters(self, value):
        return all([0 < v <= 100 for v in value])

    @tailcone_diameters.validator
    def tailcone_diameters(self, value):
        return all([0 < v <= 100 for v in value])

    @tailcone_diameters_pos.validator
    def tailcone_diameters_pos(self, value):
        return all([0 <= v <= 100 for v in value])

    # inner geometry variables
    cabinfloor_height = Input(2.2, private=not (__name__ == '__main__'))  # [m]
    cargofloor_height = Input(3.8, private=not (__name__ == '__main__'))  # [m]
    cabinfloor_thickness = Input(0.15, validator=Positive())  # [m]
    cargofloor_thickness = Input(0.15, validator=Positive())  # [m]

    @cabinfloor_height.validator  # check that cabin floor is inside fuselage
    def cabinfloor_height(self, value):
        return value < self.d_inner

    @cargofloor_height.validator  # check that cargo floor is inside fuselage and below cabin
    def cargofloor_height(self, value):
        return self.d_inner > value > self.cabinfloor_height

    structure_transparency = Input(0.8, validator=Range(0, 1))

    # ----- NOSE SECTION ----- #
    # The nosecone section is shown geometrically by subtracting an inner solid from an outer
    # one to obtain a shell.

    @Part
    def outer_nosecone_profiles(self):
        return Circle(quantify=len(self.nosecone_diameters),
                      color='Black',
                      radius=[i * self.d_outer / 100.
                              for i in self.nosecone_diameters][child.index] / 2,
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         child.index * (self.l_nosecone / (
                                                 len(self.nosecone_diameters) - 1)),
                                         Vector(0, 0, 1),
                                         self.nosecone_z_translate[child.index] / 100. *
                                         self.d_outer)
                      )

    @Part
    def inner_nosecone_profiles(self):
        return Circle(quantify=len(self.nosecone_diameters),
                      color='Black',
                      radius=[i * self.d_inner / 100.
                              for i in self.nosecone_diameters][child.index] / 2,
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         child.index * (self.l_nosecone / (
                                                 len(self.nosecone_diameters) - 1)),
                                         Vector(0, 0, 1),
                                         self.nosecone_z_translate[child.index] / 100. *
                                         self.d_outer)
                      )

    @Part(in_tree=False)
    def outer_nosecone_section(self):
        return LoftedSolid(profiles=self.outer_nosecone_profiles)

    @Part(in_tree=False)
    def inner_nosecone_section(self):
        return LoftedSolid(profiles=self.inner_nosecone_profiles)

    @Part
    def nosecone_section(self):
        return SubtractedSolid(shape_in=self.outer_nosecone_section,
                               tool=self.inner_nosecone_section,
                               color='Gray',
                               transparency=self.structure_transparency,
                               mesh_deflection=1e-3)

    # ----- CYLINDRICAL SECTION ----- #
    # The cylindrical section is shown geometrically by subtracting an inner solid from an outer
    # one to obtain a shell.

    @Part
    def outer_cylindrical_profiles(self):
        return Circle(radius=self.d_outer / 2, quantify=2, color='Black',
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         self.l_nosecone + child.index * self.l_cylindrical))

    @Part
    def inner_cylindrical_profiles(self):
        return Circle(radius=self.d_inner / 2,
                      quantify=2, color='Black',
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         self.l_nosecone + child.index * self.l_cylindrical))

    @Part(in_tree=False)
    def outer_cylindrical_section(self):
        return LoftedSolid(profiles=self.outer_cylindrical_profiles)

    @Part(in_tree=False)
    def inner_cylindrical_section(self):
        return LoftedSolid(profiles=self.inner_cylindrical_profiles)

    @Part
    def cylindrical_section(self):
        return SubtractedSolid(shape_in=self.outer_cylindrical_section,
                               tool=self.inner_cylindrical_section,
                               color='Gray',
                               transparency=self.structure_transparency,
                               mesh_deflection=1e-3)

    # ----- TAIL SECTION ----- #
    # The tailcone section is shown geometrically by subtracting an inner solid from an outer
    # one to obtain a shell.

    @Part
    def outer_tailcone_profiles(self):
        return Circle(quantify=len(self.tailcone_diameters),
                      color='Black',
                      radius=[i * self.d_outer / 100. for i in
                              self.tailcone_diameters][child.index] / 2,
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         self.l_nosecone + self.l_cylindrical + 0.01 *
                                         self.tailcone_diameters_pos[ child.index] *
                                         self.l_tailcone,
                                         Vector(0, 0, 1),
                                         self.tailcone_z_translate[child.index] / 100. *
                                         self.d_outer)
                      )

    @Part
    def inner_tailcone_profiles(self):
        return Circle(quantify=len(self.tailcone_diameters),
                      color='Black',
                      radius=[i * self.d_inner / 100. for i in
                              self.tailcone_diameters][child.index] / 2,
                      position=translate(self.position.rotate90('y'),
                                         Vector(1, 0, 0),
                                         self.l_nosecone + self.l_cylindrical + 0.01 *
                                         self.tailcone_diameters_pos[child.index] *
                                         self.l_tailcone,
                                         Vector(0, 0, 1),
                                         self.tailcone_z_translate[child.index] / 100. *
                                         self.d_outer)
                      )

    @Part(in_tree=False)
    def outer_tailcone_section(self):
        return LoftedSolid(profiles=self.outer_tailcone_profiles)

    @Part(in_tree=False)
    def inner_tailcone_section(self):
        return LoftedSolid(profiles=self.inner_tailcone_profiles)

    @Part
    def tailcone_section(self):
        return SubtractedSolid(shape_in=self.outer_tailcone_section,
                               tool=self.inner_tailcone_section,
                               color='Gray',
                               transparency=self.structure_transparency,
                               mesh_deflection=1e-3)

    # ----- FLOORS ----- #
    # The cabin and cargo floors are obtained by finding the common of a rectangle with
    # thickness of cabinfloor or cargofloor thickness with the inner sections defined in the
    # previous sections.

    @Part(in_tree=False)
    def cabin_floor_uncut(self):
        return Box(self.x_cabin_floor_end, self.d_outer,
                   self.cabinfloor_thickness,
                   position=translate(self.position,
                                      'Y', -self.d_outer / 2,
                                      'Z', self.d_inner / 2 -
                                      self.cabinfloor_height -
                                      self.cabinfloor_thickness))

    @Part
    def cabin_floor(self):
        return Common(shape_in=self.cabin_floor_uncut,
                      tool=[self.inner_cylindrical_section,
                            self.inner_nosecone_section,
                            self.inner_tailcone_section],
                      color='Gray')

    @Part(in_tree=False)
    def cargo_floor_uncut(self):
        return Box(self.x_cabin_floor_end, self.d_outer, self.cargofloor_thickness,
                   position=translate(self.position,
                                      'Y', -self.d_outer / 2,
                                      'Z', self.d_inner / 2 - self.cargofloor_height -
                                      self.cargofloor_thickness))

    @Part
    def cargo_floor(self):
        return Common(shape_in=self.cargo_floor_uncut,
                      tool=[self.inner_cylindrical_section,
                            self.inner_nosecone_section,
                            self.inner_tailcone_section],
                      color='Gray')

    # ----- REAR PRESSURE BULKHEAD ----- #
    # The rear pressure bulkhead is a common of a simple box with the inner fuselage section.
    # Realistically, it would in fact be curved, but this simplification is good enough for this
    # analysis.

    @Part
    def aft_pressure_bulkhead(self):
        return Common(shape_in=Box((self.d_outer - self.d_inner) / 2,
                                   self.d_inner,
                                   self.d_inner,
                                   position=translate(self.position,
                                                      'x', self.x_cabin_floor_end,
                                                      'y', -0.5 * self.d_inner,
                                                      'z', -0.5 * self.d_inner)),
                      tool=[self.inner_tailcone_section,
                            self.inner_cylindrical_section],
                      color='Gray')


# if run as main file, display
if __name__ == '__main__':
    from parapy.gui import display

    obj = FuselageStructure()
    display(obj)
