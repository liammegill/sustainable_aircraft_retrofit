from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
import os
from hydrogen_aircraft import AIRFOIL_DIR


class Airfoil(FittedCurve):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Airfoil

    Authors: Liam Megill & Tom Hoogerdijk

    Defines an airfoil curve. This class is of the superclass FittedCurve. Scales for chord length
    and thickness to chord ratio. The class defaults a NACA0012 airfoil of chord length 1.

    Chord in metres.
    """
    chord = Input(1., validator=Positive)  # [m]
    airfoil_name = Input("NACA0012", validator=IsInstance(str))
    tc = Input(1., validator=Range(0., 100., incl_max=True))  # [%] if 1 then thickness to chord
    # ratio is taken as the same as the airfoil .dat file
    mesh_deflection = Input(0.0001)

    @Attribute
    def tc_airfoildata(self):
        """Returns thickness to chord ratio of raw airfoil .dat file if self.tc != 1"""
        if self.tc != 1:
            with open(os.path.join(AIRFOIL_DIR, self.airfoil_name + '.dat'), 'r') as f:
                point_lst1 = []
                for line in f:
                    x, z = line.split(' ', 1)
                    point_lst1.append([float(x), float(z)])

            i = int((len(point_lst1) - 1) / 2)
            lst_tophalf = point_lst1[:i + 1]
            lst_bothalf = point_lst1[i:]
            lst_bothalf2 = lst_bothalf[::-1]

            return max([lst_tophalf[j][1] - lst_bothalf2[j][1]] for j in range(len(lst_tophalf)))[
                       0] * 100
        else:
            return 1

    @Attribute
    def points(self):
        """Returns scaled list of points"""
        with open(os.path.join(AIRFOIL_DIR, self.airfoil_name + '.dat'), 'r') as f:
            point_lst = []
            for line in f:
                x, z = line.split(' ', 1)
                point_lst.append(self.position.translate(
                    "x", float(x) * self.chord,
                    "z", float(z) * self.chord * (self.tc / self.tc_airfoildata)
                ))
        return point_lst


if __name__ == '__main__':
    from parapy.gui import display

    obj = Airfoil()
    display(obj)
