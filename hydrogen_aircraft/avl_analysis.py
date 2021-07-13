from parapy.core import *
from parapy.geom import *
import kbeutils.avl as avl
from parapy.core.validate import *


class AvlAnalysis(Base):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: AvlAnalysis

    Authors: Liam Megill & Tom Hoogerdijk

    AVL analysis of aircraft in midcruise using the kbeutils implementation of AVL
    """

    name = Input('A320', validator=IsInstance(str))
    mach = Input(0.78, validator=Range(0.0, 0.99, incl_min=True, incl_max=True))  # [-]
    mac = Input(4.1935, validator=Positive() and is_real_number)  # [m]
    ref_span = Input(35.8, validator=Positive() and is_real_number)  # [m]
    ref_area = Input(122.6, validator=Positive() and is_real_number)  # [m2]
    ref_point = Input(Point(0, 0, 0))
    cl = Input(0.0, validator=is_real_number)  # [-]
    cd0 = Input(0.018, validator=is_real_number and Positive())  # [-]
    avl_surfaces = Input()

    @Input
    def cruise_case(self):
        return [('cruise', {'alpha': avl.Parameter(name='alpha', value=self.cl,
                                                   setting='CL')})]

    @Attribute
    def avl_configuration(self):
        """AVL configuration"""
        return avl.Configuration(name='Airbus ' + self.name,
                                 reference_area=self.ref_area,
                                 reference_chord=self.mac,
                                 reference_span=self.ref_span,
                                 reference_point=self.ref_point,
                                 mach=self.mach,
                                 surfaces=self.avl_surfaces,
                                 cd_p=self.cd0)

    @Part
    def avl_cases(self):
        """AVL cases"""
        return avl.Case(quantify=len(self.cruise_case),
                        name=self.cruise_case[child.index][0],
                        settings=self.cruise_case[child.index][1])

    @Part
    def interface(self):
        """AVL interface"""
        return avl.Interface(configuration=self.avl_configuration,
                             cases=self.avl_cases)
