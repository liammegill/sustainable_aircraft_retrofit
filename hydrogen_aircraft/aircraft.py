from parapy.core import *
from parapy.geom import *
from parapy.core.snapshot import write_snapshot, read_snapshot
from parapy.core.validate import *
from parapy.exchange.step import STEPWriter
import numpy as np
import os
from datetime import *
from parapy.gui.display import get_top_window
from parapy.gui.camera import MinimalCamera
from hydrogen_aircraft import Fuselage, AvlAnalysis, LiftingSurface, Turbofan, COGVisualisation, \
    range_equation, isa_calculator, center_of_gravity_x, write_output_txt_file, \
    create_payload_range_diagram
from tkinter import Tk, messagebox

DIR = os.path.dirname(__file__)


class Aircraft(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Aircraft

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Monday 19th April 2021

    Main class for KBE assignment of a single-aisle hydrogen retrofitted aircraft. This file is
    the main Aircraft class which can be instantiated to obtain the whole aircraft. The main
    inputs are n_firstclass_rows, n_economy_rows, n_seats_port_firstclass and ..._economy.
    n_seats_starboard_firstclass and ..._economy, which can also be added as an external input
    txt file.
    """

    ###############################################################################################
    # Inputs
    ###############################################################################################
    baseline_aircraft = Input('A320')

    # seat inputs
    n_firstclass_rows = Input(3, private=True,)
    n_economy_rows = Input(18, private=True,)
    n_seats_port_firstclass = Input(2, private=True,
                                    validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_port_economy = Input(3, private=True,
                                 validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_starboard_firstclass = Input(2, private=True,
                                         validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_starboard_economy = Input(3, private=True,
                                      validator=And(IsInstance(int), Positive(incl_zero=True)))

    # Aircraft
    cruise_mach_number = Input(0.78)  # [-]
    cruise_altitude = Input(11280.)  # [m] from Janes
    cd0_cruise = Input(0.018, validator=Positive())  # [-]
    # from https://junzis.com/files/openap_dragpolar.pdf
    fuel_fractions_roskam = Input([0.990, 0.995, 0.995, 0.985, 0.990, 0.995])

    @Input
    def fuel_fractions_hydrogen(self):
        return [1 - (1 - fuel_fraction) * 42.8 / 142 *
                self.efficiency_power_conv_kero / self.efficiency_power_conv_h2
                for fuel_fraction in self.fuel_fractions_roskam]

    efficiency_power_conv_kero = Input(0.3, validator=Range(0, 1))
    efficiency_power_conv_h2 = Input(0.3, validator=Range(0, 1))

    reserve_fuel_percentage = Input(5, validator=Range(0, 20, incl_min=True, incl_max=True))  # [%]

    # Propulsion System
    n_engines = Input(2, validator=Positive() and IsInstance(int))
    engine_centerline_y = Input(5.75, validator=Positive() and is_real_number)  # [m]
    engine_front_x = Input(11.14, validator=Positive() and is_real_number)  # [m]
    engine_length = Input(2.6, validator=Positive() and is_real_number)  # [m]

    # Fuel tank
    tank_volume_fraction = Input(0.92)  # [-] from the Cryo-V report
    tank_weight_fraction = Input(1.1)  # [-]

    # Main wing, vertical tail and horizontal stabilizer inputs
    wing_fraction_x = Input(0.32579, validator=Range(-1., 1., incl_min=True, incl_max=True))

    @wing_fraction_x.validator
    def wing_fraction_x(self, value):
        if (value * self.fuselage.l_fuselage) < (self.fuselage.nosebox_end_x *
                                                 self.fuselage.l_nosecone):
            return False, f'The main wing is located such that the leading edge intersects with ' \
                          f'the nosebox. Increase wing_fraction_x such that the main wing does ' \
                          f'not intersect with the nosebox. Try 0.33.'
        else:
            return True

    wing_fraction_z = Input(-0.2294, private=True, validator=Range(-1., 1., incl_min=True,
                                                                   incl_max=True))
    horztail_fraction_x = Input(0.60, validator=Range(-1., 1., incl_min=True, incl_max=True))
    horztail_fraction_z = Input(0.1694, private=True, validator=Range(-1., 1., incl_min=True,
                                                                      incl_max=True))
    verttail_fraction_x = Input(0.44, validator=Range(-1., 1., incl_min=True, incl_max=True))
    verttail_fraction_z = Input(0.36, private=True, validator=Range(-1., 1., incl_min=True,
                                                                    incl_max=True))
    mainwing_span = Input(34.10, validator=Positive())  # [m]
    mainwing_c_root = Input(6.07, validator=Positive())  # [m]
    mainwing_c_kink = Input(3.84, validator=Positive())  # [m]
    mainwing_c_tip = Input(1.64, validator=Positive())  # [m]
    mainwing_kink = Input(True, private=True, validator=IsInstance(bool))
    mainwing_kinkloc = Input(6.604, validator=Positive())  # [m]

    @mainwing_kinkloc.validator
    def mainwing_kinkloc(self, value):
        if self.mainwing_kink:
            if self.mainwing_semispan < value:
                return False, f'The distance from the aircraft\'s centerline to the kink ' \
                              f'location {value} [m] is greater than the semispan of the wing. ' \
                              f'Input an kink distance that is less that ' \
                              f'{self.mainwing_semispan} [m]'
            elif 0. > value:
                return False, 'The float entered is negative. All lengths and distances must be ' \
                              'positive.'
            else:
                return True
        return True

    mainwing_tc_root = Input(16.5, validator=Positive())  # [%]
    mainwing_tc_kink = Input(11.8, validator=Positive())  # [%]
    mainwing_tc_tip = Input(10.8, validator=Positive())  # [%]
    mainwing_incidence = Input(4.9, validator=is_real_number)  # [deg]
    mainwing_twist_kink = Input(0.65, validator=is_real_number)  # [deg]
    mainwing_twist_tip = Input(-0.5, validator=is_real_number)  # [deg]
    mainwing_dihedral = Input(5., validator=is_real_number)  # [deg]
    mainwing_sweep = Input(25., validator=is_real_number)  # [deg]
    mainwing_airfoil_root = Input('NACA23015', validator=IsInstance(str))
    mainwing_airfoil_kink = Input('NACA23015', validator=IsInstance(str))
    mainwing_airfoil_tip = Input('NACA23015', validator=IsInstance(str))
    horztail_span = Input(12.45, validator=Positive())  # [m]
    horztail_sweep = Input(29, validator=Positive())  # [deg]
    horztail_c_root = Input(3.92, validator=Positive())  # [m]
    horztail_c_tip = Input(1.24, validator=Positive())  # [m]
    horztail_dihedral = Input(6, validator=is_real_number)  # [deg]
    horztail_kink = Input(False, validator=IsInstance(bool))
    verttail_span = Input(6.26, validator=Positive())  # [m]
    verttail_c_root = Input(5.729, validator=Positive())  # [m]
    verttail_c_tip = Input(1.774, validator=Positive())  # [m]
    verttail_sweep = Input(40.7, validator=Positive())  # [deg]
    verttail_kink = Input(False, validator=IsInstance(bool))
    empennage_airfoil = Input('NACA0015', validator=IsInstance(str))

    ###############################################################################################
    # Attributes
    ###############################################################################################

    @Attribute
    def max_payload_range(self):
        return range_equation(self.fuel_mass, self.maximum_takeoff_mass,
                              self.reserve_fuel_percentage, self.fuel_fractions_hydrogen,
                              self.cruise_mach_number, self.cruise_speed_of_sound,
                              self.port_turbofan.tsfc_cal, self.cl_cd)

    @Attribute
    def ferry_range(self):
        return range_equation(self.fuel_mass, self.operational_empty_mass + self.fuel_mass,
                              self.reserve_fuel_percentage, self.fuel_fractions_hydrogen,
                              self.cruise_mach_number, self.cruise_speed_of_sound,
                              self.port_turbofan.tsfc_cal, self.cl_cd)

    @Attribute
    def n_passengers(self):
        return self.fuselage.n_pax

    @Attribute
    def cog_of_mac(self):
        """Aircraft's x_cg position as % of the MAC [%]"""
        return ((self.aircraft_cog_x - self.x_mac) / self.mac) * 100

    # Aircraft mass
    @Attribute
    def pax_mass(self):
        """Mass of all passengers in [kg]"""
        return self.fuselage.n_pax * 90

    @Attribute
    def cargo_mass(self):
        """Mass of all cargo in [kg]"""
        return 161 * (self.fuselage.n_cargo_containers_fore + self.fuselage.n_cargo_containers_aft
                      ) * self.root.fuselage.cargo_containers_fore[0].cargo_container.volume

    @Attribute
    def maximum_takeoff_mass(self):
        """Maximum takeoff mass in [kg]"""
        return self.operational_empty_mass + self.pax_mass + self.cargo_mass + self.fuel_mass

    @Attribute
    def fuel_mass(self):
        """Mass of all fuel in [kg]"""
        return self.fuselage.total_tank_volume * self.tank_volume_fraction * self.rho_lh2

    @Attribute
    def tank_mass(self):
        """Mass of LH2 tanks in [kg]"""
        return self.fuel_mass * self.tank_weight_fraction

    @Attribute
    def operational_empty_mass(self):
        """Operational empty mass in [kg]"""
        return self.aircraft_cog_analysis[2]

    # Wing Attributes

    @Attribute
    def taper_in(self):
        """Inboard taper ratio [-] if the main wing has a kink"""
        if self.mainwing_kink:
            return self.mainwing_c_kink / self.mainwing_c_root

    @Attribute
    def taper_out(self):
        """Outboard taper ratio [-] if the main wing has a kink"""
        if self.mainwing_kink:
            return self.mainwing_c_tip / self.mainwing_c_kink

    @Attribute
    def taper(self):
        """Taper ratio [-] if the main wing has no kink"""
        if not self.mainwing_kink:
            return self.mainwing_c_tip / self.mainwing_c_root

    @Attribute
    def mainwing_semispan(self):
        """Semispan in [m]"""
        return self.mainwing_span / 2

    @Attribute(in_tree=not (lambda self: self.mainwing_kink))
    def planform_area_in(self):
        """Inboard surface area of wing [m2] if the main wing has a kink"""
        if self.mainwing_kink:
            return self.mainwing_kinkloc * self.mainwing_c_root * (
                    1 + self.taper_in)

    @Attribute(in_tree=not (lambda self: self.mainwing_kink))
    def planform_area_out(self):
        """Outboard surface area of wing [m2] if the main wing has a kink"""
        if self.mainwing_kink:
            return (self.mainwing_semispan - self.mainwing_kinkloc) * self.mainwing_c_kink * (
                    1 + self.taper_out)

    @Attribute
    def planform_area(self):
        """Surface area in [m2]"""
        if self.mainwing_kink:
            return self.planform_area_out + self.planform_area_in
        else:
            return self.mainwing_semispan * self.mainwing_c_root * (
                    1 + self.taper)

    @Attribute
    def aspect_ratio(self):
        """Aspect ratio [-]"""
        return (self.mainwing_span ** 2) / self.planform_area

    @Attribute(in_tree=not (lambda self: self.mainwing_kink))
    def mac_in(self):
        """Inboard MAC [m] if the main wing has a kink"""
        if self.mainwing_kink:
            return (2 / 3) * self.mainwing_c_root * (
                    (1 + self.taper_in + self.taper_in ** 2) / (1 + self.taper_in))

    @Attribute(in_tree=not (lambda self: self.mainwing_kink))
    def mac_out(self):
        """Outboard MAC [m] if the main wing has a kink"""
        if self.mainwing_kink:
            return (2 / 3) * self.mainwing_c_kink * (
                    (1 + self.taper_out + self.taper_out ** 2) / (1 + self.taper_out))

    @Attribute  # MAC [m]
    def mac(self):
        """Mean aerodynamic chord (MAC) [m]"""
        if self.mainwing_kink:
            return (self.mac_in * self.planform_area_in + self.mac_out * self.planform_area_out) \
                   / self.planform_area
        else:
            return (2 / 3) * self.mainwing_c_root * ((1 + self.taper + self.taper ** 2) / (1 +
                                                                                           self.taper))

    @Attribute
    def y_mac(self):
        """Spanwise location of MAC from centerline in [m]"""
        return (self.mac_in * self.planform_area_in + (self.mainwing_kinkloc + self.mac_out) *
                self.planform_area_out) / self.planform_area

    @Attribute
    def x_mac(self):
        """LEMAC position in [m]"""
        return self.wing_fraction_x * self.fuselage.l_fuselage + np.tan(
            np.radians(self.mainwing_sweep)) * self.y_mac

    @Attribute
    def oswald_efficiency(self):
        """Oswald efficiency factor (e) taken from AVL [-]"""
        return self.avl_interface.results['cruise']['Totals']['e']

    # AVL attributes
    @Attribute
    def avl_surfaces(self):
        """All instances of AVL surface definition"""
        return [self.right_mainwing_root.avl_surface, self.right_horztail_root.avl_surface,
                self.verttail_root.avl_surface]

    @Attribute
    def cl_cruise(self):
        """CL required during midcruise"""
        return (self.midcruise_weight * 9.81) / \
               (0.5 * isa_calculator(self.cruise_altitude)[2] *
                ((self.cruise_mach_number * np.sqrt(1.4 * 287.085 * isa_calculator(
                    self.cruise_altitude)[0])) ** 2)
                * self.planform_area)

    @Attribute
    def avl_interface(self):
        """AVL interface"""
        return AvlAnalysis(name=self.baseline_aircraft,
                           ref_area=self.planform_area,
                           avl_surfaces=self.avl_surfaces,
                           ref_span=self.mainwing_span,
                           mac=self.mac,
                           mach=self.cruise_mach_number,
                           cl=self.cl_cruise,
                           cd0=self.cd0_cruise).interface

    @Attribute
    def cl_cd(self):
        """Aircraft lift to drag ratio during cruise"""
        cl = self.avl_interface.results['cruise']['Totals']['CLtot']
        cd = self.avl_interface.results['cruise']['Totals']['CDtot']
        return cl / cd

    # Miscellaneous attributes
    lhv_lh2 = Attribute(120.0)  # [MJ/kg]
    rho_lh2 = Attribute(70.85)  # [kg/m3]

    @Attribute
    def aircraft_cog_analysis(self):
        """Aircraft x c.g. position"""
        return center_of_gravity_x(
            mainwing_cog_x=self.right_mainwing.cog.x,
            horztail_cog_x=self.right_horztail.cog.x,
            verttail_cog_x=self.verttail.cog.x,
            fuselage_cog_x=0.45 * self.fuselage.l_fuselage,
            tank1_cog_x=self.fuselage.fwd_hydrogen_tank.tank_cylindrical_section.cog.x if
            self.fuselage.n_hydrogen_tanks == 2 else 0,
            w_tank1=self.fuselage.fwd_hydrogen_tank.tank_volume * self.rho_lh2 * 0.9 if
            self.fuselage.n_hydrogen_tanks == 2 else 0,
            w_tank1_fuel=self.fuselage.fwd_hydrogen_tank.tank_volume * self.rho_lh2 * 1.0 if
            self.fuselage.n_hydrogen_tanks == 2 else 0,
            tank2_cog_x=self.fuselage.aft_hydrogen_tank.tank_cylindrical_section.cog.x,
            w_tank2=self.fuselage.aft_hydrogen_tank.tank_volume * self.rho_lh2 * 0.9,
            w_tank2_fuel=self.fuselage.aft_hydrogen_tank.tank_volume * self.rho_lh2 * 1.0,
            mainwing_wingbox_cog_x=self.fuselage.mainwing_wingbox.cog.x,
            apu_cog_x=self.fuselage.auxiliary_power_unit.shape_in.cog.x,
            nosebox_cog_x=self.fuselage.nosebox.direct_children[0].cog.x,
            nlg_cog_x=self.fuselage.nlg_cog_x,
            engine_cog_x=self.fuselage.mainwing_wingbox_x_start + (self.engine_length / 2),
            pylon_cog_x=self.fuselage.mainwing_wingbox_x_start + self.engine_length,
            pilot_cog_x=self.fuselage.cockpit_seats[0].position.x + ((2 / 3) *
                                                                     self.fuselage.cockpit_seats
                                                                     [0].seat_depth),
            firstclassseats_cog_x=[
                self.fuselage.port_firstclass_rows[i].simple_seat_volume.cog.x
                for i in np.arange(self.fuselage.n_firstclass_rows)],
            economyseats_cog_x=[self.fuselage.port_economy_rows[i].simple_seat_volume.cog.x for
                                i in np.arange(self.fuselage.n_economy_rows)],
            cargocontainer_cog_x=[self.fuselage.cargo_containers_fore[i].container_uncut.cog.x
                                  for
                                  i in np.arange(self.fuselage.n_cargo_containers_fore)],
            cargocontainer_vol=self.root.fuselage.cargo_containers_fore[
                0].cargo_container.volume,
            n_firstclassseats_row=self.fuselage.n_seats_port_firstclass +
                                  self.fuselage.n_seats_starboard_firstclass,
            n_economyseats_row=self.fuselage.n_seats_port_economy +
                               self.fuselage.n_seats_starboard_economy)

    @Attribute
    def aircraft_cog_x(self):
        """Aircraft x c.g. position"""
        return self.aircraft_cog_analysis[0]

    @Attribute
    def mainwing_wingbox_x_start(self):
        """Fwd x position of the wing box. The leading edge of the airfoil that intersects
            the fuselage"""
        return min(self.right_mainwing.edges[0].sample_points[idx].x for idx in range(len(
            self.right_mainwing.edges[0].sample_points)))

    @Attribute
    def mainwing_wingbox_x_end(self):
        """Aft x position of the wing box. The trailing edge of the airfoil that intersects
                the fuselage"""
        return self.right_mainwing.vertices[0].point.x

    @Attribute
    def midcruise_weight(self):
        return (self.maximum_takeoff_mass *
                (self.fuel_fractions_roskam[0] * self.fuel_fractions_roskam[1]
                 * self.fuel_fractions_roskam[2] * self.fuel_fractions_roskam[
                     3] * self.fuel_fractions_roskam[4] +
                 self.fuel_fractions_roskam[0] * self.fuel_fractions_roskam[1]
                 * self.fuel_fractions_roskam[2] * self.fuel_fractions_roskam[3])) / 2

    @Attribute
    def cruise_speed_of_sound(self):
        """Speed of sound at cruise altitude in  [m/s]"""
        return np.sqrt(1.4 * 287.085 * isa_calculator(self.cruise_altitude)[0])

    @Attribute
    def total_cruise_thrust(self):
        """Calculate thrust required to balance drag during cruise [N] """
        return self.midcruise_weight * 9.81 / self.cl_cd

    ###############################################################################################
    # Actions
    ###############################################################################################

    @action(label='Save snapshot to .json file')  # save all modified values to .json file
    def save_full_aircraft(self):
        save_name = 'saves\\save_{date:%Y-%m-%d_%H%M%S}.json'.format(date=datetime.now())
        with open(save_name, 'w') as save_file:
            write_snapshot(self, save_file)

        return messagebox.showinfo(title='Success',
                                   message='Instance successfully written to ' + save_name)

    @action(label='Export geometry to .stp file')
    def stepwriter_components(self):
        filename = 'output/' + 'Airbus_' + self.baseline_aircraft + \
                   '_{date:%Y-%m-%d_%H%M%S}'.format(date=datetime.now()) + ".stp"
        STEPWriter(filename=filename,
                   nodes=[self.right_mainwing,
                          self.left_mainwing,
                          self.right_horztail,
                          self.left_horztail,
                          self.verttail],
                   trees=[self.fuselage]).write()
        return messagebox.showinfo(title='Success',
                                   message='Aircraft geometry successfully written to ' + filename)

    @action(label='Write output .txt file')
    def write_output_file(self):
        filename = 'output/' + 'Airbus_' + self.baseline_aircraft + '_' + \
                   '{date:%Y-%m-%d_%H%M%S}'.format(date=datetime.now())
        write_output_txt_file(aircraft=self.baseline_aircraft,
                              filename=filename,
                              output_list= \
                                  [['Total tank volume', self.fuselage.total_tank_volume, '[m3]'],
                                   ['Total tank mass', self.tank_mass, '[kg]'],
                                   ['Total fuel mass', self.fuel_mass, '[kg]'],
                                   ['Fuselage length', self.fuselage.l_fuselage, '[m]'],
                                   ['Cabin length', self.fuselage.l_cabin, '[m]'],
                                   ['PAX', self.n_passengers, '[-]'],
                                   ['No. first class rows',
                                    self.fuselage.n_firstclass_rows, '[-]'],
                                   ['First class config.',
                                    str(self.fuselage.n_seats_port_firstclass) + '-'
                                    + str(self.fuselage.n_seats_starboard_firstclass), '[-]'],
                                   ['No. economy class rows',
                                    self.fuselage.n_economy_rows, '[-]'],
                                   ['Economy class config.',
                                    str(self.fuselage.n_seats_port_economy) + '-'
                                    + str(self.fuselage.n_seats_starboard_economy), '[-]'],
                                   ['No. cargo containers fwd',
                                    self.fuselage.n_cargo_containers_fore, '[-]'],
                                   ['No. cargo containers aft',
                                    self.fuselage.n_cargo_containers_aft, '[-]']],
                              aero_analysis=self.port_turbofan.aero_engine_calculations,
                              avl_results=self.avl_interface.results['cruise'],
                              cl_cd=self.cl_cd,
                              cg_mac=self.cog_of_mac,
                              cg_analysis=self.aircraft_cog_analysis,
                              r_ferry=self.ferry_range,
                              r_maxpayload=self.max_payload_range)
        return messagebox.showinfo(title='Success',
                                   message='Output file successfully written to ' +
                                           filename + '.txt')

    @action(label='Print views to .jpg files')
    def create_images(self):
        filename_num = '{date:%Y-%m-%d_%H%M%S}'.format(date=datetime.now())

        main_window = get_top_window()
        viewer = main_window.viewer

        filename_image1 = 'Airbus_' + self.baseline_aircraft + '_top_view_' + filename_num + '.jpg'
        viewer.set_camera(MinimalCamera(viewing_center=Point(0, 0, 0),
                                        eye_location=Point(0, 0, 5),
                                        up_direction=Vector(0, 1, 0),
                                        scale=4, aspect_ratio=1.5))
        viewer.fit_all()
        main_window.viewer.save_image('output/' + filename_image1)

        filename_image2 = 'Airbus_' + self.baseline_aircraft + '_side_view_' + filename_num + \
                          '.jpg'
        viewer.set_camera(MinimalCamera(viewing_center=Point(0, 0, 0),
                                        eye_location=Point(0, -5, 0),
                                        up_direction=Vector(0, 0, 1),
                                        scale=4, aspect_ratio=1.5))
        viewer.fit_all()
        main_window.viewer.save_image('output/' + filename_image2)

        filename_image3 = 'Airbus_' + self.baseline_aircraft + '_iso_view_' + filename_num + \
                          '.jpg'
        viewer.set_camera(MinimalCamera(viewing_center=Point(0, 0, 0),
                                        eye_location=Point(-5, -5, 3),
                                        up_direction=Vector(0, 0, 1),
                                        scale=4, aspect_ratio=1.5))
        viewer.fit_all()
        main_window.viewer.save_image('output/' + filename_image3)

        return messagebox.showinfo(title='Success',
                                   message='Images successfully written to ' + '/output/')

    # Analysis actions

    @action(label='Plot and export payload range diagram')
    def payload_range_diagram(self):
        return create_payload_range_diagram(self.max_payload_range, self.pax_mass +
                                            self.cargo_mass, self.ferry_range,
                                            self.baseline_aircraft)

    @action(label='Plot and export climb rate diagram')
    def climb_rate_diagram(self):
        return self.port_turbofan.create_climb_rate_diagram()

    # AVL actions

    @action(label='Show geometry in AVL')
    def avl_geometry(self):
        return self.avl_interface.show_geometry()

    @action(label='Show Trefftz plot')
    def avl_trefftzplot(self):
        return self.avl_interface.show_trefftz_plot()

    ###############################################################################################
    # Parts
    ###############################################################################################

    @Part
    def fuselage(self):
        return Fuselage(pass_down='n_firstclass_rows, n_economy_rows, n_seats_port_firstclass, '
                                  'n_seats_port_economy, n_seats_starboard_firstclass, '
                                  'n_seats_starboard_economy, mainwing_wingbox_x_start, '
                                  'mainwing_wingbox_x_end')

    @Part(in_tree=False)
    def right_mainwing_root(self):
        return LiftingSurface(name='mainwing',
                              kink=self.mainwing_kink,
                              span=self.mainwing_span,
                              kink_loc=self.mainwing_kinkloc,
                              airfoil_root=self.mainwing_airfoil_root,
                              airfoil_kink=self.mainwing_airfoil_kink,
                              airfoil_tip=self.mainwing_airfoil_tip,
                              tc_root=self.mainwing_tc_root,
                              tc_kink=self.mainwing_tc_kink,
                              tc_tip=self.mainwing_tc_tip,
                              chord_root=self.mainwing_c_root,
                              chord_kink=self.mainwing_c_kink,
                              chord_tip=self.mainwing_c_tip,
                              dihedral=self.mainwing_dihedral,
                              sweep=self.mainwing_sweep,
                              incidence=self.mainwing_incidence,
                              twist_kink=self.mainwing_twist_kink,
                              twist_tip=self.mainwing_twist_tip,
                              mirrored=True,
                              position=translate(self.position,
                                                 "x", self.wing_fraction_x *
                                                 self.fuselage.l_fuselage,
                                                 "z",
                                                 self.wing_fraction_z *
                                                 self.fuselage.d_outer))

    @Part
    def right_mainwing(self):
        return SubtractedSolid(
            shape_in=self.right_mainwing_root.lofted_solid,
            tool=self.fuselage.fus_structure.inner_cylindrical_section,
            color='gray',
            mesh_deflection=0.0001)

    @Part
    def left_mainwing(self):
        return MirroredShape(shape_in=self.right_mainwing,
                             reference_point=self.position,
                             vector1=self.position.Vz,
                             vector2=self.position.Vx,
                             mesh_deflection=0.0001,
                             color='gray')

    @Part
    def port_turbofan(self):
        return Turbofan(pass_down='baseline_aircraft, maximum_takeoff_mass, cruise_altitude,'
                                  'cruise_mach_number, n_engines, planform_area, aspect_ratio,'
                                  'oswald_efficiency, total_cruise_thrust',
                        zero_lift_drag_coefficient=self.cd0_cruise)

    @Part(in_tree=False)
    def right_horztail_root(self):
        return LiftingSurface(name='horztail',
                              kink=False,
                              airfoil_root=self.empennage_airfoil,
                              airfoil_tip=self.empennage_airfoil,
                              chord_root=self.horztail_c_root,
                              chord_tip=self.horztail_c_tip,
                              span=self.horztail_span,
                              dihedral=self.horztail_dihedral,
                              sweep=self.horztail_sweep,
                              mirrored=True,
                              position=translate(self.position,
                                                 "x",
                                                 self.fuselage.l_cylindrical +
                                                 self.fuselage.l_nosecone +
                                                 (self.horztail_fraction_x *
                                                  self.fuselage.l_tailcone),
                                                 "z",
                                                 self.horztail_fraction_z *
                                                 self.fuselage.d_outer))

    @Part
    def right_horztail(self):
        return SubtractedSolid(
            shape_in=self.right_horztail_root.lofted_solid,
            tool=self.fuselage.fus_structure.inner_tailcone_section,
            color='gray',
            mesh_deflection=0.0001)

    @Part
    def left_horztail(self):
        return MirroredShape(shape_in=self.right_horztail,
                             reference_point=self.position,
                             vector1=self.position.Vz,
                             vector2=self.position.Vx,
                             mesh_deflection=0.0001,
                             color='gray')

    @Part(in_tree=False)
    def verttail_root(self):
        return LiftingSurface(name='verttail',
                              kink=False,
                              airfoil_root=self.empennage_airfoil,
                              airfoil_tip=self.empennage_airfoil,
                              chord_root=self.verttail_c_root,
                              chord_tip=self.verttail_c_tip,
                              span=self.verttail_span * 2,
                              sweep=self.verttail_sweep,
                              mirrored=False,
                              position=rotate(translate(self.position,
                                                        "x",
                                                        self.fuselage.l_cylindrical +
                                                        self.fuselage.l_nosecone +
                                                        (self.verttail_fraction_x *
                                                         self.fuselage.l_tailcone),
                                                        "z",
                                                        self.verttail_fraction_z *
                                                        self.fuselage.d_outer),
                                              "x", np.radians(90)))

    @Part
    def verttail(self):
        return SubtractedSolid(
            shape_in=self.verttail_root.lofted_solid,
            tool=self.fuselage.fus_structure.inner_tailcone_section,
            color='gray',
            mesh_deflection=0.0001)

    @Part
    def cog_visualisation(self):
        return COGVisualisation(pass_down='mac, x_mac, mainwing_span, aircraft_cog_x',
                                position=self.position)


# if run as main file, load object
if __name__ == '__main__':

    # ask user if a previous save should be opened
    from tkinter import Tk, messagebox
    from tkinter.filedialog import askopenfilename

    Tk().withdraw()
    user_answer = messagebox.askyesno('Open previous save',
                                      'Welcome to the hydrogen retrofit of a single-aisle '
                                      'aircraft KBE application.\nDo you want to open a '
                                      'previous save (will ignore input file)?')
    if user_answer:
        old_save_path = askopenfilename(title='Open previous save',
                                        filetypes=[('json', '.json')])
        with open(old_save_path) as f:
            obj = read_snapshot(f)

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

    from parapy.gui import display

    display(obj, autodraw=True)
