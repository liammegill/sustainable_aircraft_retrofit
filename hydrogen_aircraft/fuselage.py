from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
import numpy as np
from hydrogen_aircraft import FuselageStructure, Seat, CargoContainer, HydrogenTank


class Fuselage(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Fuselage

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines a fuselage for a single-aisle aircraft. Includes the fuselage structure,
    cabin layout with two-class seating, overhead storage, cargo storage, cockpit, wingbox,
    nose landing gear storage and hydrogen tanks at the rear of the aircraft. Validators are
    present for all inputs to ensure that the aircraft remains realistic. The class defaults to
    an Airbus A320.
    """

    # ----- INPUTS ----- #
    # seats, passed down from aircraft
    n_aisles = Input(1, validator=OneOf([1]))  # at the moment, only single aisle is available
    n_firstclass_rows = Input(3)
    n_economy_rows = Input(12)
    n_seats_port_firstclass = Input(2, validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_port_economy = Input(3, validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_starboard_firstclass = Input(2,
                                         validator=And(IsInstance(int), Positive(incl_zero=True)))
    n_seats_starboard_economy = Input(3, validator=And(IsInstance(int), Positive(incl_zero=True)))

    @Attribute  # calculate number of passengers
    def n_pax(self):
        return self.n_firstclass_rows * (self.n_seats_port_firstclass +
                                         self.n_seats_starboard_firstclass) + \
               self.n_economy_rows * (self.n_seats_port_economy + self.n_seats_starboard_economy)

    seat_pitch_economy = Input(0.74)  # [m]
    seat_pitch_firstclass = Input(0.9)
    seat_width_economy = Input(0.43, validator=GreaterThan(0.3))  # [m]
    seat_width_firstclass = Input(0.5, validator=GreaterThan(0.3))  # [m]
    seat_height = Input(1.00, validator=GreaterThan(0.8))  # [m]
    seat_depth = Input(0.5, validator=GreaterThan(0.4))  # [m]
    armrest_width = Input(0.05, validator=GreaterThan(0.03))
    seat_clearance = Input(0.05, validator=Positive())
    headroom_height = Input(1.6)  # [m]

    @seat_pitch_economy.validator
    def seat_pitch_economy(self, value):
        return value > self.seat_depth

    @headroom_height.validator
    def headroom_height(self, value):
        return value > self.seat_height + 0.5

    # outer geometry variables
    d_outer = Input(4.14)  # [m]
    skin_thickness = Input(0.1, validator=Positive())  # [m]

    @d_outer.validator
    def d_outer(self, value):
        return value > self.skin_thickness

    @Attribute
    def d_inner(self):
        return self.d_outer - 2 * self.skin_thickness

    l_fuselage = Input(37.57)  # [m]
    l_nosecone = Input(5.44, validator=Positive())  # [m]
    l_tailcone = Input(13.47, validator=Positive())  # [m]

    @l_fuselage.validator
    def l_fuselage(self, value):
        return value > self.l_nosecone + self.l_tailcone

    @Attribute
    def l_cylindrical(self):
        return self.l_fuselage - self.l_nosecone - self.l_tailcone

    # inner geometry variables
    divider_wall_thickness = Input(0.05, validator=Positive())  # [m]
    l_cockpit = Input(4.)  # [m]
    l_cockpit_instruments = Input(2.4, validator=Positive())  # [m]

    @l_cockpit.validator  # ensures enough space available for the pilots
    def l_cockpit(self, value):
        return value > self.l_cockpit_instruments + 1.2

    # cabin
    cabinfloor_height = Input(2.2)  # [m]
    l_galley = Input(0.76, validator=Positive())
    w_galley = Input(0.91, validator=Positive())
    l_toilet = Input(0.91, validator=Positive())
    w_toilet = Input(0.91, validator=Positive())
    l_cross_aisle = Input(1.0, validator=GreaterThan(0.8))  # [m]
    minimum_aisle_width = Input(0.5, validator=GreaterThan(0.45))  # [m]

    @cabinfloor_height.validator  # check that cabin floor is inside fuselage
    def cabinfloor_height(self, value):
        return value < self.d_inner

    # cargo
    cargofloor_height = Input(3.8)  # [m]
    cargo_spacing = Input(0.1, validator=Positive())  # [m]
    cargo_container_height = Input(1.143)  # [m] for LD3-45
    cargo_container_width = Input(2.438)  # [m]
    cargo_container_depth = Input(1.534)  # [m]
    cargo_container_base = Input(1.562)  # [m]

    @Attribute
    def fwd_cargo_start(self):
        """"Position of the start of the fwd cargo hold"""
        return Position(
            location=Point((self.nosebox_end_x * self.l_nosecone) + self.cargo_spacing, 0,
                           (self.d_inner / 2 - self.cargofloor_height)),
            orientation=Orientation(x=Vector(1, 0, 0), y=Vector(0, 1, 0),
                                    z=Vector(0, 0, 1)))

    @Attribute
    def aft_cargo_start(self):
        """"Position of the start of the aft cargo hold"""
        return Position(location=Point(self.mainwing_wingbox_x_end + self.cargo_spacing, 0,
                                       (self.d_inner / 2 - self.cargofloor_height)),
                        orientation=Orientation(x=Vector(1, 0, 0), y=Vector(0, 1, 0),
                                                z=Vector(0, 0, 1)))

    @Attribute(validator=Positive and is_real_number)
    def l_cargohold_fore(self):
        """Length of the fwd cargo hold [m]"""
        return self.mainwing_wingbox_x_start - self.nosebox_end_x * self.l_nosecone

    @Attribute(validator=Positive and is_real_number)
    def l_cargohold_aft(self):
        """Length of the aft cargo hold [m]"""
        return min((self.fus_structure.x_cabin_floor_end - self.mainwing_wingbox_x_end),
                   ((self.l_nosecone+self.l_cylindrical) - self.mainwing_wingbox_x_end))

    @Attribute(validator=Positive and IsInstance(int))
    def n_cargo_containers_fore(self):
        """Number of cargo containers in the fwd cargo hold"""
        return int(self.l_cargohold_fore / (self.cargo_container_depth +
                   self.cargo_spacing))

    @Attribute(validator=Positive and IsInstance(int))
    def n_cargo_containers_aft(self):
        """Number of cargo containers in the aft cargo hold"""
        return int(self.l_cargohold_aft / (self.cargo_container_depth +
                   self.cargo_spacing))

    @cargofloor_height.validator  # check that cargo floor is inside fuselage and below cabin
    def cargofloor_height(self, value):
        return self.d_inner > value > self.cabinfloor_height

    # Wing box and Nose box
    nosebox_end_x = Input(1.2, validator=Positive())  # [-] fraction of l_nosecone
    mainwing_wingbox_x_start = Input(13, validator=Positive() and is_real_number)  # [m]
    mainwing_wingbox_x_end = Input(18, validator=Positive() and is_real_number)  # [m]

    # doors and windows
    door_width_type1 = Input(0.81, validator=GreaterThan(0.7))  # [m]
    door_height_type1 = Input(1.85, validator=GreaterThan(1.3))  # [m]
    cabin_window_width = Input(0.24, validator=GreaterThan(0.2))  # [m]
    cabin_window_height = Input(0.41, validator=GreaterThan(0.2))  # [m]
    cabin_window_spacing = Input(0.56, validator=GreaterThan(0.4))  # [m]
    cabin_window_overfloor = Input(0.8, validator=Range(0.6, 0.9))  # [m]

    @Attribute
    def xcab_cabin_windows(self):
        return self.xcab_fwd_crossaisle + 0.03 + self.door_width_type1 + \
               self.cabin_window_spacing * 0.5

    @Attribute
    def n_cabin_windows(self):
        distance = self.xcab_aft_toilet - self.xcab_cabin_windows
        return int(distance / self.cabin_window_spacing)

    # hydrogen storage
    n_hydrogen_tanks = Input(2, validator=OneOf([1, 2]))
    aft_limit_hydrogen_tank = Input(0.85)  # [-] multiple of l_fuselage

    @aft_limit_hydrogen_tank.validator
    def aft_limit_hydrogen_tank(self, value):
        return self.x_tank_begin / self.l_fuselage < value < 1.

    # ----- LENGTHS AND LOCATIONS ----- #

    @Attribute
    def l_cabin(self):
        return self.xcab_aft_bulkhead + self.skin_thickness

    @Attribute
    def x_cabin(self):
        return self.l_cockpit

    @Attribute
    def full_cabin_width(self):
        return 2 * np.sqrt(
            (self.d_inner / 2) ** 2 - (self.cabinfloor_height - self.d_inner / 2) ** 2)

    @Attribute
    def cabin_width(self):
        if self.seat_height > 2 * (self.cabinfloor_height - self.d_inner / 2):
            w_cabin = 2 * np.sqrt((self.d_inner / 2) ** 2 - (self.seat_height -
                                                             self.cabinfloor_height +
                                                             self.d_inner / 2) ** 2)
        else:
            w_cabin = self.full_cabin_width
        return w_cabin

    @Attribute
    def aisle_width_economy(self):
        return (self.cabin_width - (self.n_seats_port_economy +
                                    self.n_seats_starboard_economy) *
                self.seat_width_economy - ((self.n_seats_port_economy +
                                            self.n_seats_starboard_economy) *
                                           self.n_aisles + 1) * self.armrest_width -
                2 * self.seat_clearance) / self.n_aisles

    @aisle_width_economy.on_slot_change
    # TODO: figure out why number is not changing in tree
    def check_economy_aisle(self):
        num_reduction = 0
        while self.aisle_width_economy < self.minimum_aisle_width:
            lst = [self.n_seats_port_economy, self.n_seats_starboard_economy]
            idx = lst.index(max(lst))
            if idx == 0:
                self.n_seats_port_economy -= 1
            else:
                self.n_seats_starboard_economy -= 1
            num_reduction += 1

        if num_reduction > 0:
            from tkinter import Tk, messagebox
            Tk().withdraw()
            messagebox.showwarning('Aisle width too small',
                                   'The aisle width is below its defined minimum. Therefore, '
                                   'the number of economy seats has been reduced by ' + str(
                                       num_reduction))
        return

    @Attribute
    def aisle_width_firstclass(self):
        return (self.cabin_width - (self.n_seats_port_firstclass +
                                    self.n_seats_starboard_firstclass) *
                self.seat_width_firstclass - ((self.n_seats_port_firstclass +
                                               self.n_seats_starboard_firstclass) *
                                              self.n_aisles + 1) * self.armrest_width -
                2 * self.seat_clearance) / self.n_aisles

    @aisle_width_firstclass.on_slot_change
    # TODO: figure out why number is not changing in tree
    def check_firstclass_aisle(self):
        num_reduction = 0
        while self.aisle_width_firstclass < self.minimum_aisle_width:
            lst = [self.n_seats_port_firstclass, self.n_seats_starboard_firstclass]
            idx = lst.index(max(lst))
            if idx == 0:
                self.n_seats_port_firstclass -= 1
            else:
                self.n_seats_starboard_firstclass -= 1
            num_reduction += 1

        if num_reduction > 0:
            from tkinter import Tk, messagebox
            Tk().withdraw()
            messagebox.showwarning('Aisle width too small',
                                   'The aisle width is below its defined minimum. Therefore, '
                                   'the number of first class seats has been reduced by ' + str(
                                       num_reduction))
        return

    @Attribute
    def nlg_cog_x(self):
        return 0.85 * (self.nosebox_end_x * self.l_nosecone)

    # cabin lengths
    # xcab is local x position with respect to start of cabin
    # TODO: suppress lengths if certain things do not exist (eg. no first class seating)

    @Attribute
    def xcab_fwd_crossaisle(self):
        return max([self.l_toilet, self.l_galley])

    @Attribute
    def xcab_fwd_divider(self):
        return self.xcab_fwd_crossaisle + self.l_cross_aisle

    @Attribute
    def xcab_firstclass_seats(self):
        return self.xcab_fwd_divider + self.divider_wall_thickness

    @Attribute
    def xcab_class_divider(self):
        return self.xcab_firstclass_seats + self.n_firstclass_rows * self.seat_pitch_firstclass

    @Attribute
    def xcab_economy_seats(self):
        return self.xcab_class_divider + self.divider_wall_thickness

    @Attribute
    def xcab_aft_divider(self):
        return self.xcab_economy_seats + self.n_economy_rows * self.seat_pitch_economy

    @Attribute
    def xcab_aft_toilet(self):
        return self.xcab_aft_divider + self.divider_wall_thickness

    @Attribute
    def xcab_aft_crossaisle(self):
        return self.xcab_aft_toilet + self.l_toilet

    @Attribute
    def xcab_aft_galley(self):
        return self.xcab_aft_crossaisle + self.l_cross_aisle

    @Attribute
    def xcab_aft_bulkhead(self):
        return self.xcab_aft_galley + self.l_galley

    @xcab_aft_bulkhead.validator
    def xcab_aft_bulkhead(self, value):
        if value + self.x_cabin < self.mainwing_wingbox_x_end:
            msg = f'The aircraft layout is such that the main wing intersects with the aft ' \
                  f'pressure bulkhead. Increase the length of the cabin, for example by ' \
                  f'increasing the number of rows in economy. Or move the location of ' \
                  f'the main wing forward'
            return False, msg

        elif value + self.x_cabin > 0.85 * self.l_fuselage:
            msg = f'The aft pressure bulkhead is located to far aft. Reduce the number of rows ' \
                  f'in the cabin'
            return False, msg

        else:
            return True

    # ----- PARTS ----- #

    # create fuselage structure
    @Part
    def fus_structure(self):
        return FuselageStructure(pass_down='d_outer, d_inner, l_fuselage, l_nosecone, '
                                           'l_tailcone, cabinfloor_height, cargofloor_height',
                                 x_cabin_floor_end=self.x_cabin + self.xcab_aft_bulkhead)

    # create cockpit (simplified)
    @Part(in_tree=False)
    def cockpit_window_cutout(self):
        return Box(self.l_cockpit * 0.7,
                   self.d_outer,
                   self.d_outer * 0.1,
                   position=translate(self.position,
                                      'y', -0.5 * self.d_outer,
                                      'z', self.d_outer * 0.15))

    @Part
    def cockpit_window(self):
        return Common(shape_in=self.cockpit_window_cutout,
                      tool=self.fus_structure.nosecone_section,
                      transparency=0.5,
                      color='lightblue')

    @Part
    def cockpit_instruments(self):
        return Subtracted(Common(shape_in=Box(self.l_cockpit_instruments,
                                              self.d_inner,
                                              self.cabinfloor_height - self.d_inner / 2
                                              + 0.15 * self.d_outer,
                                              position=translate(self.position,
                                                                 'y', -0.5 * self.d_outer,
                                                                 'z', self.d_inner / 2
                                                                 - self.cabinfloor_height)),
                                 tool=self.fus_structure.inner_nosecone_section),
                          tool=self.cockpit_window_cutout,
                          color='gray')

    @Part
    def cockpit_seats(self):
        return Seat(n_seats=1,
                    type='pilot',
                    quantify=2,
                    position=translate(self.position,
                                       'x', self.l_cockpit_instruments + 0.2,
                                       'y', -0.2 - self.seat_width_firstclass + child.index * (
                                               0.4 + self.seat_width_firstclass),
                                       'z', self.d_inner / 2 - self.cabinfloor_height))

    # ----- CREATE CABIN ----- #
    # Most of the parts are commons using the inner fuselage and simple boxes. The boxes are not
    # shown as separate parts to reduce the number of parts in the fuselage.

    @Part(in_tree=False)  # simple box for positioning purposes
    def cabin(self):
        return Box(1, 1, 1, position=translate(self.position,
                                               'x', self.x_cabin,
                                               'z', self.d_inner / 2 - self.cabinfloor_height))

    @Part(in_tree=False)
    def aisle_for_cutting(self):
        return Box(self.l_cabin,
                   self.aisle_width_economy * 1.5,
                   self.cabinfloor_height,
                   position=translate(self.cabin.position,
                                      'y', -0.5 * self.aisle_width_economy * 1.5))

    @Part
    def cockpit_divider(self):
        return Common(shape_in=Box(self.divider_wall_thickness,
                                   self.d_inner,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'x', -self.divider_wall_thickness,
                                                      'y', -self.d_inner / 2)),
                      tool=[self.fus_structure.inner_nosecone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='Gray')

    @Part
    def fwd_galley(self):
        return Common(shape_in=Box(self.l_galley,
                                   self.w_galley,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'y', self.full_cabin_width / 2 -
                                                      self.w_galley)),
                      tool=[self.fus_structure.inner_nosecone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='lightgreen')

    @Part
    def fwd_toilet(self):
        return Common(shape_in=Box(self.l_toilet,
                                   self.w_toilet,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'y', -self.full_cabin_width / 2)),
                      tool=[self.fus_structure.inner_nosecone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='lightblue')

    @Part
    def fwd_doors(self):
        return Common(shape_in=Box(self.door_width_type1,
                                   self.d_outer,
                                   self.door_height_type1,
                                   position=translate(self.cabin.position,
                                                      'x', self.xcab_fwd_crossaisle + 0.03,
                                                      'y', -self.d_outer / 2)),
                      tool=[self.fus_structure.nosecone_section,
                            self.fus_structure.cylindrical_section])

    @Part
    def fwd_divider(self):
        return Subtracted(shape_in=Common(shape_in=Box(self.divider_wall_thickness,
                                                       self.d_outer,
                                                       self.cabinfloor_height,
                                                       position=translate(self.cabin.position,
                                                                          'x',
                                                                          self.xcab_fwd_divider,
                                                                          'y', -self.d_inner / 2)),
                                          tool=[self.fus_structure.inner_cylindrical_section,
                                                self.fus_structure.inner_nosecone_section]),
                          tool=self.aisle_for_cutting)

    @Part
    def port_firstclass_rows(self):
        return Seat(seat_width=self.seat_width_firstclass,
                    seat_height=self.seat_height,
                    seat_depth=self.seat_depth,
                    n_seats=self.n_seats_port_firstclass,
                    color='Red',
                    quantify=self.n_firstclass_rows,
                    position=translate(self.cabin.position,
                                       'y', -0.5 * self.cabin_width,
                                       'x',
                                       self.xcab_firstclass_seats + self.seat_pitch_firstclass -
                                       self.seat_depth + child.index * self.seat_pitch_firstclass))

    @Part
    def starboard_firstclass_rows(self):
        return Seat(seat_width=self.seat_width_firstclass,
                    seat_height=self.seat_height,
                    seat_depth=self.seat_depth,
                    n_seats=self.n_seats_starboard_firstclass,
                    color='Red',
                    quantify=self.n_firstclass_rows,
                    position=translate(self.cabin.position,
                                       'y',
                                       0.5 * self.cabin_width - self.n_seats_starboard_firstclass *
                                       self.seat_width_firstclass - self.armrest_width -
                                       self.seat_clearance,
                                       'x',
                                       self.xcab_firstclass_seats + self.seat_pitch_firstclass -
                                       self.seat_depth + child.index * self.seat_pitch_firstclass))

    @Part
    def class_divider(self):
        return Subtracted(shape_in=Common(shape_in=Box(self.divider_wall_thickness,
                                                       self.d_outer,
                                                       self.cabinfloor_height,
                                                       position=translate(self.cabin.position,
                                                                          'x',
                                                                          self.xcab_class_divider,
                                                                          'y', -self.d_inner / 2)),
                                          tool=[self.fus_structure.inner_cylindrical_section,
                                                self.fus_structure.inner_nosecone_section]),
                          tool=self.aisle_for_cutting,
                          suppress=not (self.n_firstclass_rows > 0 and self.n_economy_rows > 0))

    @Part
    def port_economy_rows(self):
        return Seat(seat_width=self.seat_width_economy,
                    seat_height=self.seat_height,
                    seat_depth=self.seat_depth,
                    n_seats=self.n_seats_port_economy,
                    color='Red',
                    quantify=self.n_economy_rows,
                    position=translate(self.cabin.position,
                                       'y', -0.5 * self.cabin_width + self.seat_clearance,
                                       'x',
                                       self.xcab_economy_seats + self.seat_pitch_economy -
                                       self.seat_depth + child.index * self.seat_pitch_economy))

    @Part
    def starboard_economy_rows(self):
        return Seat(seat_width=self.seat_width_economy,
                    seat_height=self.seat_height,
                    seat_depth=self.seat_depth,
                    n_seats=self.n_seats_starboard_economy,
                    color='Red',
                    quantify=self.n_economy_rows,
                    position=translate(self.cabin.position,
                                       'y',
                                       0.5 * self.cabin_width - self.n_seats_starboard_economy *
                                       self.seat_width_economy - self.armrest_width -
                                       self.seat_clearance,
                                       'x',
                                       self.xcab_economy_seats + self.seat_pitch_economy -
                                       self.seat_depth + child.index * self.seat_pitch_economy))

    @Part
    def aft_divider(self):
        return Subtracted(shape_in=Common(shape_in=Box(self.divider_wall_thickness,
                                                       self.d_outer,
                                                       self.cabinfloor_height,
                                                       position=translate(self.cabin.position,
                                                                          'x',
                                                                          self.xcab_aft_divider,
                                                                          'y', -self.d_inner / 2)),
                                          tool=[self.fus_structure.inner_cylindrical_section,
                                                self.fus_structure.inner_tailcone_section]),
                          tool=self.aisle_for_cutting)

    @Part
    def aft_port_toilet(self):
        return Common(shape_in=Box(self.l_toilet,
                                   self.w_toilet,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'y', -self.full_cabin_width / 2,
                                                      'x', self.xcab_aft_toilet)),
                      tool=[self.fus_structure.inner_tailcone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='lightblue')

    @Part
    def aft_starboard_toilet(self):
        return Common(shape_in=Box(self.l_toilet,
                                   self.w_toilet,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'y',
                                                      self.full_cabin_width / 2 - self.w_toilet,
                                                      'x', self.xcab_aft_toilet)),
                      tool=[self.fus_structure.inner_tailcone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='lightblue')

    @Part
    def aft_doors(self):
        return Common(shape_in=Box(self.door_width_type1,
                                   self.d_outer,
                                   self.door_height_type1,
                                   position=translate(self.cabin.position,
                                                      'x', self.xcab_aft_crossaisle + 0.03,
                                                      'y', -self.d_outer / 2)),
                      tool=[self.fus_structure.tailcone_section,
                            self.fus_structure.cylindrical_section])

    @Part
    def aft_galley(self):
        return Common(shape_in=Box(self.l_galley,
                                   self.d_inner,
                                   self.cabinfloor_height,
                                   position=translate(self.cabin.position,
                                                      'y', -0.5 * self.full_cabin_width,
                                                      'x', self.xcab_aft_galley)),
                      tool=[self.fus_structure.inner_tailcone_section,
                            self.fus_structure.inner_cylindrical_section],
                      color='lightgreen')

    # ----- WINDOWS ----- #
    # The windowsare created using a common of the compound of multiple boxes that intersect the
    # fuselage.

    @Part(in_tree=False)
    def cabin_window_cutboxes(self):
        return Box(self.cabin_window_width,
                   self.d_outer,
                   self.cabin_window_height,
                   quantify=self.n_cabin_windows,
                   position=translate(self.cabin.position,
                                      'x',
                                      self.xcab_cabin_windows + 0.5 * (self.cabin_window_spacing
                                                                       - self.cabin_window_width) +
                                      child.index * self.cabin_window_spacing,
                                      'y', -self.d_outer / 2,
                                      'z', self.cabin_window_overfloor))

    @Part
    def cabin_windows(self):
        return Common(shape_in=Compound(built_from=self.cabin_window_cutboxes),
                      tool=[self.fus_structure.nosecone_section,
                            self.fus_structure.tailcone_section,
                            self.fus_structure.cylindrical_section],
                      transparency=0.5,
                      color='lightblue')

    # ----- OVERHEAD STORAGE ----- #

    @Part
    def overhead_storage_firstclass(self):
        return Subtracted(Common(shape_in=Box(self.xcab_class_divider -
                                              self.xcab_firstclass_seats,
                                              self.d_inner,
                                              self.cabinfloor_height -
                                              self.headroom_height,
                                              position=translate(self.cabin.position,
                                                                 'x', self.xcab_firstclass_seats,
                                                                 'y', -0.5 * self.d_inner,
                                                                 'z', self.headroom_height)),
                                 tool=[self.fus_structure.inner_nosecone_section,
                                       self.fus_structure.inner_cylindrical_section]),
                          tool=self.aisle_for_cutting,
                          color='white', transparency=0.3,
                          suppress=self.n_firstclass_rows == 0)

    @Part
    def overhead_storage_economy(self):
        return Subtracted(Common(shape_in=Box(self.xcab_aft_divider -
                                              self.xcab_economy_seats,
                                              self.d_inner,
                                              self.cabinfloor_height -
                                              self.headroom_height,
                                              position=translate(self.cabin.position,
                                                                 'x', self.xcab_economy_seats,
                                                                 'y', -0.5 * self.d_inner,
                                                                 'z', self.headroom_height)),
                                 tool=[self.fus_structure.inner_tailcone_section,
                                       self.fus_structure.inner_cylindrical_section]),
                          tool=self.aisle_for_cutting,
                          color='white', transparency=0.3,
                          suppress=self.n_economy_rows == 0)

    # ----- HYDROGEN TANKS ----- #
    # The hydrogen tanks are placed between two dummy limits that are used to calculate the
    # diameter of the fuselage at that location and, therefore, the maximum size of the tanks.

    @Part(in_tree=False)
    def dummy_aft_limit_tank(self):
        return Common(shape_in=Box(0.01, self.d_inner, self.d_inner,
                                   position=translate(self.position,
                                                      'x', self.aft_limit_hydrogen_tank *
                                                      self.l_fuselage,
                                                      'y', -0.5 * self.d_inner,
                                                      'z', -0.5 * self.d_inner)),
                      tool=[self.fus_structure.inner_tailcone_section,
                            self.fus_structure.inner_cylindrical_section])

    @Part(in_tree=False)
    def dummy_mid_limit_tank(self):
        return Common(shape_in=Box(0.01, self.d_inner, self.d_inner,
                                   position=translate(self.position,
                                                      'x', self.x_tank_begin +
                                                      self.available_tank_length / 2,
                                                      'y', -0.5 * self.d_inner,
                                                      'z', -0.5 * self.d_inner)),
                      tool=[self.fus_structure.inner_tailcone_section,
                            self.fus_structure.inner_cylindrical_section],
                      suppress=self.n_hydrogen_tanks == 1)

    @Attribute
    def aft_limit_tank_diameter(self):
        return self.dummy_aft_limit_tank.oriented_bbox.height

    @Attribute
    def mid_limit_tank_diameter(self):
        return self.dummy_mid_limit_tank.oriented_bbox.height

    @Attribute
    def x_tank_begin(self):
        return self.x_cabin + self.xcab_aft_bulkhead + self.skin_thickness

    """
    @x_tank_begin.validator
    def x_tank_begin(self, value):
        if self.n_hydrogen_tanks == 2:
            if value > (self.aft_limit_hydrogen_tank - self.mid_limit_tank_diameter):
                msg = 'There is no room for any tank, reduce the number of rows'
                return False, msg
            else:
                return True
        else:
            if value > (self.aft_limit_hydrogen_tank - self.aft_limit_tank_diameter):
                msg = 'There is no room for any tank, reduce the number of rows'
                return False, msg
            else:
                return True
   """

    @Attribute
    def available_tank_length(self):
        return self.aft_limit_hydrogen_tank * self.l_fuselage - self.x_tank_begin

    @Part
    def fwd_hydrogen_tank(self):
        return HydrogenTank(tank_outer_diameter=self.mid_limit_tank_diameter - 0.1,
                            tank_cylindrical_length=self.available_tank_length / 2 -
                                                    self.mid_limit_tank_diameter - 0.1,
                            position=translate(self.position,
                                               'x', self.x_tank_begin + 0.05,
                                               'z',
                                               self.dummy_mid_limit_tank.oriented_bbox.center.z),
                            suppress=self.n_hydrogen_tanks == 1)

    @Part
    def aft_hydrogen_tank(self):
        return HydrogenTank(tank_outer_diameter=self.aft_limit_tank_diameter - 0.1,
                            tank_cylindrical_length=self.available_tank_length / 2 -
                                                    self.aft_limit_tank_diameter - 0.1 if
                            self.n_hydrogen_tanks == 2 else self.available_tank_length -
                                                            self.aft_limit_tank_diameter - 0.1,
                            position=translate(self.position,
                                               'x', self.x_tank_begin + 0.05 +
                                               self.available_tank_length / 2 if
                                               self.n_hydrogen_tanks == 2 else
                                               self.x_tank_begin + 0.05,
                                               'z',
                                               self.dummy_aft_limit_tank.oriented_bbox.center.z))

    @Attribute
    def total_tank_volume(self):
        if self.n_hydrogen_tanks == 1:
            return self.aft_hydrogen_tank.tank_volume
        else:
            return self.fwd_hydrogen_tank.tank_volume + self.aft_hydrogen_tank.tank_volume

    # ----- CARGO ----- #
    @Part
    def cargo_containers_fore(self):
        return CargoContainer(quantify=self.n_cargo_containers_fore,
                              position=translate(self.fwd_cargo_start,
                                                 'x', child.index * (self.cargo_container_depth +
                                                                     self.cargo_spacing),
                                                 'y', - 0.5 * self.cargo_container_width))

    @Part
    def cargo_containers_aft(self):
        return CargoContainer(quantify=self.n_cargo_containers_aft,
                              position=translate(self.aft_cargo_start,
                                                 'x', child.index * (self.cargo_container_depth +
                                                                     self.cargo_spacing),
                                                 'y', - 0.5 * self.cargo_container_width))

    # ----- MISCELLANEOUS ----- #

    @Part
    def auxiliary_power_unit(self):
        return Common(shape_in=Box(0.05 * self.l_fuselage,
                                   self.d_inner,
                                   self.d_inner,
                                   position=translate(self.position,
                                                      'x', 0.95 * self.l_fuselage,
                                                      'y', -0.5 * self.d_inner,
                                                      'z', -0.5 * self.d_inner)),
                      tool=self.fus_structure.inner_tailcone_section,
                      color='gray')

    @Part
    def mainwing_wingbox(self):
        return CommonSolid(
            shape_in=Box(self.mainwing_wingbox_x_end - self.mainwing_wingbox_x_start,
                         self.d_inner,
                         self.d_outer - self.cabinfloor_height
                         - self.fus_structure.cabinfloor_thickness -
                         self.skin_thickness,
                         position=translate(self.position,
                                            "x", self.mainwing_wingbox_x_start,
                                            "y", -self.d_outer / 2,
                                            "z", -self.d_outer / 2)),
            tool=[self.fus_structure.inner_nosecone_section,
                  self.fus_structure.inner_cylindrical_section,
                  self.fus_structure.inner_tailcone_section],
            color='gray')

    @Part
    def nosebox(self):
        return Common(shape_in=Box((self.nosebox_end_x * self.l_nosecone) - 0.5,
                                   self.d_outer,
                                   self.d_outer - self.cabinfloor_height
                                   - self.fus_structure.cabinfloor_thickness -
                                   self.skin_thickness,
                                   position=translate(self.position,
                                                      "x", 0.5,
                                                      "y", -self.d_outer / 2,
                                                      "z", -self.d_outer / 2)),
                      tool=[self.fus_structure.inner_nosecone_section,
                            self.fus_structure.inner_cylindrical_section,
                            self.fus_structure.inner_tailcone_section],
                      color='gray')


if __name__ == '__main__':
    from parapy.gui import display

    obj = Fuselage()
    display(obj)
