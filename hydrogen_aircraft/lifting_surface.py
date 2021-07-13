from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
import kbeutils.avl as avl
import numpy as np
from tkinter import Tk, messagebox
from hydrogen_aircraft import Airfoil


class LiftingSurface(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: LiftingSurface

    Authors: Liam Megill & Tom Hoogerdijk

    Defines lifting surface and avl surface for an AVL analysis. Can be used for
    all lifting surfaces found on the aircraft. If the lifting surface is used to define avl
    surfaces the lifting surface is hidden as much as possible in the geometry view. The
    class defaults a very simple wing.

    All quantities in metres.
    """

    # Inputs
    name = Input('liftingsurface', validator=IsInstance(str))
    avl_liftingsurface = Input(False, validator=IsInstance(bool))
    kink = Input(False, validator=IsInstance(bool))
    mirrored = Input(True, validator=IsInstance(bool))

    airfoil_root = Input("NACA0012", validator=IsInstance(str))
    airfoil_kink = Input("NACA0012", validator=IsInstance(str))
    airfoil_tip = Input("NACA0012", validator=IsInstance(str))

    chord_root = Input(6., validator=Positive and is_real_number)  # [m]
    chord_kink = Input(3., validator=Positive and is_real_number)  # [m]
    chord_tip = Input(3., validator=Positive and is_real_number)  # [m]
    tc_root = Input(1., validator=is_real_number)  # [%] thickness to chord ratio of airfoil
    tc_kink = Input(1., validator=is_real_number)  # [%] if 1 then ratio is taken ...
    tc_tip = Input(1., validator=is_real_number)  # [%] ... as the same as the airfoil .dat file

    span = Input(34.09, validator=Positive and is_real_number)  # [m]
    kink_loc = Input(10., validator=Positive(incl_zero=True) and is_real_number)  # [m] from
    # aircraft centerline

    @kink_loc.validator
    def kink_loc(self, value):
        if self.kink:
            if (self.span/2) < value:
                return False, f'The distance from the aircraft\'s centerline to the kink ' \
                              f'location {value} [m] is greater than the semispan of the ' \
                              f'lifting surface. Input an kink distance that is less that ' \
                              f'{self.span/2} [m]'
            elif 0. > value:
                return False, 'The float entered is negative. All lengths and distances must be ' \
                              'positive.'
            else:
                return True
        return True

    dihedral = Input(0., validator=is_real_number)  # [deg]
    sweep = Input(0., validator=is_real_number)  # [deg]
    incidence = Input(0., validator=is_real_number)  # [deg]
    twist_kink = Input(0., validator=is_real_number)  # [deg]
    twist_tip = Input(0., validator=is_real_number)  # [deg]

    @Attribute
    def profiles(self):
        """Lifting surface profile list"""
        if self.kink:
            return [self.root_airfoil, self.kink_airfoil, self.tip_airfoil]
        else:
            return [self.root_airfoil, self.tip_airfoil]

    @Part
    def root_airfoil(self):
        """Root airfoil (fitted curve) at incidence angle to VX at aircraft centerline"""
        return Airfoil(airfoil_name=self.airfoil_root,
                       chord=self.chord_root,
                       tc=self.tc_root,
                       position=rotate(self.position, "y", np.radians(self.incidence)),
                       color='black')

    @Part
    def kink_airfoil(self):
        """Kink airfoil (fitted curve) at twist angle to VX and spanwise position from centerline.
        Suppressed if lifting surface doesn't have a kink."""
        return Airfoil(airfoil_name=self.airfoil_kink,
                       chord=self.chord_kink,
                       tc=self.tc_kink,
                       position=translate(
                           rotate(self.position, "y", np.radians(self.twist_kink)),
                           "y", self.kink_loc,
                           "x", self.kink_loc * np.tan(np.radians(self.sweep)),
                           "z", self.kink_loc * np.tan(np.radians(self.dihedral))),
                       suppress=not self.kink,
                       color='black')

    @Part
    def tip_airfoil(self):
        """Tip airfoil (fitted curve) at twist angle to VX and spanwise position from centerline"""
        return Airfoil(airfoil_name=self.airfoil_tip,
                       chord=self.chord_tip,
                       tc=self.tc_tip,
                       position=translate(
                           rotate(self.position, "y", np.radians(self.twist_tip)),
                           "y", self.span / 2,
                           "x", (self.span / 2) * np.tan(np.radians(self.sweep)),
                           "z", (self.span / 2) * np.tan(np.radians(self.dihedral))),
                       color='black')

    @Part
    def root_avl_section(self):
        """AVL section definition of root airfoil"""
        return avl.SectionFromCurve(curve_in=self.root_airfoil,
                                    color='black')

    @Part  # TODO theres is a bug with the angle if airfoil is not a NACA airfoil
    def kink_avl_section(self):
        """AVL section definition of kink airfoil. Suppressed if lifting surface doesn't have a
        kink."""
        return avl.SectionFromCurve(curve_in=self.kink_airfoil,
                                    suppress=not self.kink,
                                    color='black')

    @Part
    def tip_avl_section(self):
        """AVL section definition of tip airfoil"""
        return avl.SectionFromCurve(curve_in=self.tip_airfoil,
                                    color='black')

    @Part
    def lofted_solid(self):
        """Wing lofted solid. Hidden in lifting surface is used to define an AVL surface"""
        return LoftedSolid(profiles=self.profiles,
                           ruled=True,
                           mesh_deflection=0.0001,
                           color='gray',
                           hidden=self.avl_liftingsurface)

    @Part
    def avl_surface(self):
        """AVL surface definition"""
        return avl.Surface(name=self.name,
                           n_chordwise=12,
                           chord_spacing=avl.Spacing.cosine,
                           n_spanwise=20,
                           span_spacing=avl.Spacing.cosine,
                           y_duplicate=0.0 if self.mirrored else None,
                           sections=[self.root_avl_section, self.kink_avl_section,
                                     self.tip_avl_section] if self.kink else [
                               self.root_avl_section, self.tip_avl_section],
                           transparency=0.0 if self.avl_liftingsurface else 1.0)


if __name__ == '__main__':
    from parapy.gui import display

    obj = LiftingSurface()
    display(obj)
