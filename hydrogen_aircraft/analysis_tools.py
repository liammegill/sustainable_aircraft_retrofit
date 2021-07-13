import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
import os
from datetime import *

# lookup table of reference aircraft
aircraft_data = {'A320': {'payload_range_x': [0, 3800, 6150, 7600],
                          'payload_range_y': [19, 19, 13.5, 0],
                          'climb_rate_low': [2180, 2230, 2620, 3100, 3690, 3540, 3390, 3060, 2650,
                                             2220,
                                             1770, 1880, 1690, 1480, 1250, 940, 710],
                          'climb_rate_nom': [2140, 2160, 2450, 2800, 3010, 2880, 2750, 2490, 2130,
                                             1740, 1350, 1360, 1170, 970, 750, 470, 240],
                          'climb_rate_high': [1890, 1890, 2140, 2440, 2520, 2400, 2270, 2070, 1740,
                                              1390, 1030, 950, 750, 540, 320, 70, 0],
                          'climb_rate_hts': [0, 2000, 3000, 4000, 6000, 8000, 10000, 14000, 18000,
                                             22000, 26000, 30000, 32000, 34000, 36000, 38000,
                                             40000],
                          'climb_rate_spd': [80.8, 85.9, 97.7, 115.7, 139.9, 144.0, 148.7, 188.3,
                                             199.6, 211.9, 225.3, 236.1, 234.1, 232.0, 230.0,
                                             230.0, 230.0]
                          },
                 'A318': {'payload_range_x': [0, 3700, 6000, 7100],
                          'payload_range_y': [14.7, 14.7, 9, 0]}
                 }


def isa_calculator(h1):
    """
    ISA calculator returns temperature, pressure and density at specific altitude

    Parameters
    ----------
    h1 : float
        altitude in [m]

    Returns
    -------
    [t1, p1, d1]
        t1 in [K]
        p1 in [Pa]
        d1 in [kg/m3]
    """

    g0 = 9.80665  # [m/s]
    R = 287.0  # [J/kgK]
    tsea = 288.15  # [K]
    psea = 101325.0  # [Pa]
    dsea = 1.2250  # [kg/m3]

    if h1 <= 11000:
        a = -0.0065
        t0_k = 288.15  # kelvin
        p0 = 101325.0  # pa
        d0 = 1.2250
        h0 = 0  # m
    elif 11000 < h1 <= 20000:
        a = 0.0
        t0_k = 216.65  # kelvin
        p0 = 22632.1  # pa
        d0 = 0.363918
        h0 = 11000  # m
    elif 20000 < h1 <= 32000:
        a = +0.001
        t0_k = 216.65  # kelvin
        p0 = 5474.89  # pa
        d0 = 0.0880349
        h0 = 20000  # m
    elif 32000 < h1 <= 47000:
        a = +0.0028
        t0_k = 228.650  # kelvin
        p0 = 868.019  # pa
        d0 = 0.0132250
        h0 = 32000  # m
    elif 47000 < h1 <= 51000:
        a = 0.0
        t0_k = 270.65  # kelvin
        p0 = 110.906  # pa
        d0 = 0.00142753
        h0 = 47000  # m
    elif 51000 < h1 <= 71000:
        a = -0.0028
        t0_k = 270.65  # kelvin
        p0 = 66.9389  # pa
        d0 = 0.000861606
        h0 = 51000  # m
    elif 71000 < h1 <= 86000:
        a = -0.002
        t0_k = 214.65  # kelvin
        p0 = 3.95642  # pa
        d0 = 0.0000642110
        h0 = 71000  # m
    else:
        print("ERROR: too high")

    if a == 0:
        t1_k = t0_k + (a * (h1 - h0))
        p1_pa = p0 * math.e ** ((-g0 / (t1_k * R)) * (h1 - h0))
        d1 = p1_pa / (R * t1_k)
    else:
        t1_k = t0_k + (a * (h1 - h0))
        p1_pa = p0 * (t1_k / t0_k) ** (-g0 / (a * R))
        d1 = p1_pa / (R * t1_k)

    return [t1_k, p1_pa, d1]


def range_equation(fuel_mass, maximum_takeoff_mass, reserve_fuel_percentage,
                   fuel_fractions_hydrogen, cruise_mach_number, cruise_speed_of_sound, tsfc,
                   lift_to_drag):
    """ Calculate range that can be obtained for a given fuel mass of hydrogen """
    total_fuel_fraction = 1 - fuel_mass / (maximum_takeoff_mass
                                           * (1 + reserve_fuel_percentage / 100))
    W5W4 = total_fuel_fraction / np.prod(fuel_fractions_hydrogen)
    return cruise_mach_number * cruise_speed_of_sound / tsfc * lift_to_drag * np.log(1 / W5W4)


def create_payload_range_diagram(max_payload_range, max_payload_mass, ferry_range,
                                 comparison_aircraft):
    """ Plot payload-range diagram and compare it to a reference aircraft """

    payload_pts = [max_payload_mass / 1000, max_payload_mass / 1000, 0]
    range_pts = [0, max_payload_range / 1000, ferry_range / 1000]

    fig, ax = plt.subplots()
    ax.plot(range_pts, payload_pts, color='tab:blue', linestyle='solid', label='H2 Aircraft')
    ax.plot(aircraft_data[comparison_aircraft]['payload_range_x'],
            aircraft_data[comparison_aircraft]['payload_range_y'],
            color='tab:red', linestyle='dashed', label=comparison_aircraft)
    ax.set_xlabel('Range [km]')
    ax.set_ylabel('Payload mass [t]')
    ax.legend(loc='best')
    fig.tight_layout()

    from tkinter import Tk, messagebox
    Tk().withdraw()
    user_response = messagebox.askyesno('Save diagram',
                                        'Do you want to save the payload-range diagram?')
    if user_response:
        DIR_output = os.getcwd() + '\\output\\'
        fname = DIR_output + 'Airbus_A320_payload_range_diagram_' + '{date:%Y-%m-%d_%H%M%S}'.format(
            date=datetime.now()) + '.pdf'
        plt.savefig(fname)

    plt.show()
    return


def create_loading_diagram():
    # TODO make loading_diagram

    def potato_slice(weight_positions, weights, initial_xcg, initial_weight):
        """ Calculate single slice of the potato diagram based on weights and their position."""
        xcg_positions = [initial_xcg]
        aircraft_weight = [initial_weight]
        for xi, wi in zip(weight_positions, weights):
            sum_moments = xcg_positions[-1] * aircraft_weight[-1] + xi * wi
            sum_weights = aircraft_weight[-1] + wi
            aircraft_weight.append(sum_weights)
            xcg_positions.append(sum_moments / sum_weights)
        return xcg_positions, aircraft_weight

    # start at OEW
    # add fwd and aft cargo
    # add outboard seats front-to-back and back-to-front
    # repeat for inboard seats
    # add fuel tanks

    return


def aero_engine_code(mach, altitude, lhv, thrust, mdot_cor, BPR, max_T04,
                     Pr_fan, Pr_LPC, Pr_HPC, Pr_comb, Pr_inlet,
                     isen_fan, isen_lpc, isen_hpc, isen_lpt, isen_hpt,
                     eta_mech, eta_comb, eta_nozzle):
    """
    Aero engine code returns thrust specific fuel consumption and mass flow of fuel

    Parameters
    ----------
    mach : float
        operating mach number
    altitude : float
        altitude in [m]
    lhv : float
        lower heating value of fuel supplied in aero engine in [MJ/kg]
    thrust : float
        [N] from single engine!
    mdot_cor : float
        [kg/s]
    BPR : float
        bypass ratio
    max_T04 : float
        maximum temperature at exit of combustion chamber [K]

    Returns
    -------
    [SFC, mdot_f, T04, F_N_cal]
        SFC in [g/kNs]
        mdot_f in [kg/s]
        T04 in [K]
        F_N_cal in [N]
    """

    # TODO: finish docstring

    F_N_req = thrust

    # Constants
    R = 287  # [J/kgK]
    Pref = 101325  # [Pa]
    Tref = 288  # [K]
    cp_air = 1000  # [J/kgK]
    kappa_air = 1.4  # [-]
    cp_gas = 1150  # [J/kgK]
    kappa_gas = 1.33  # [-]

    # calculate ambient conditions
    [Ta, Pa, _] = isa_calculator(altitude)
    v_inf = mach * np.sqrt(kappa_air * R * Ta)

    out = []

    def min_func(T04):
        # Ambient
        Ta_tot = Ta * (1 + ((kappa_air - 1) / 2) * mach ** 2)
        Pa_tot = Pa * (1 + ((kappa_air - 1) / 2) * mach ** 2) ** (kappa_air / (kappa_air - 1))

        # Station 2
        T02 = Ta_tot
        P02 = Pa_tot * Pr_inlet

        # Obtaining real mass flow from corrected
        delta = Pa_tot / Pref
        theta = Ta_tot / Tref
        mdot = mdot_cor / (np.sqrt(theta) / delta)

        # mdot to core and bypass
        mdot_core = mdot / (BPR + 1)
        mdot_bypass = mdot_core * BPR

        # Fan
        P021 = Pr_fan * P02
        P013 = P021
        T021 = T02 * (1 + (1 / isen_fan) * ((P021 / P02) ** ((kappa_air - 1) / kappa_air) - 1))
        T013 = T021
        Wfan_req = mdot * cp_air * (T021 - T02)  # in W
        Wfancore = mdot_core * cp_air * (T021 - T02)

        # LPC
        P025 = Pr_LPC * P021
        T025 = T021 * (1 + (1 / isen_lpc) * ((P025 / P021) ** ((kappa_air - 1) / kappa_air) - 1))
        WLPC_req = mdot_core * cp_air * (T025 - T021)  # in W

        # Bypass nozzle calculations
        P016 = P013
        T016 = T013
        crit_press_noz_bypass = (1 - (1 / eta_nozzle) * ((kappa_air - 1) / (kappa_air + 1))) ** (
                -kappa_air / (kappa_air - 1))
        if (P016 / Pa) > crit_press_noz_bypass:
            T018 = T016 * (2 / (kappa_air + 1))
            P018 = P016 / crit_press_noz_bypass
            v18 = np.sqrt(kappa_air * R * T018)
            rho18 = P018 / (R * T018)
            A18 = mdot_bypass / (rho18 * v18)
            F_bypass = mdot_bypass * (v18 - v_inf) + A18 * (P018 - Pa)
            v18eq = (F_bypass / mdot_bypass) + v_inf
        else:
            P018 = Pa
            T018 = T016 * (1 + (1 / eta_nozzle) * (
                    (P018 / P016) ** ((kappa_air - 1) / kappa_air) - 1))
            v18 = np.sqrt(2 * cp_air * (T016 - T018))
            F_bypass = mdot_bypass * (v18 - v_inf)
            v18eq = v18

        # HPC
        P03 = Pr_HPC * P025
        T03 = T025 * (1. + (1. / isen_hpc) * (Pr_HPC ** ((kappa_air - 1.) / kappa_air) - 1.))
        WHPC_req = mdot_core * cp_air * (T03 - T025)

        # Combustion chamber
        mdot_f = (mdot_core * cp_gas * (T04 - T03)) / (eta_comb * (lhv * (10 ** 6)))  # kg/s
        mdot_corefuel = mdot_core + mdot_f
        P04 = Pr_comb * P03

        # HPT
        WHPT = WHPC_req / eta_mech
        T045 = -1. * ((WHPT / (mdot_corefuel * cp_gas)) - T04)
        P045 = P04 * ((((T045 / T04) - 1. + isen_hpt) / isen_hpt) ** (kappa_gas / (kappa_gas -
                                                                                   1.)))

        # LPT
        WLPT = (WLPC_req + Wfan_req) / eta_mech
        T05 = -1. * ((WLPT / (cp_gas * mdot_corefuel)) - T045)
        P05 = P045 * ((((T05 / T045) - 1. + isen_lpt) / isen_lpt) ** (kappa_gas / (kappa_gas - 1)))

        # Core nozzle
        P07 = P05
        T07 = T05
        crit_press_noz_core = (1 - (1 / eta_nozzle) * ((kappa_gas - 1) / (kappa_gas + 1))) ** (
                -kappa_gas / (kappa_gas - 1))
        if (P07 / Pa) > crit_press_noz_core:
            T08 = T07 * (2 / (kappa_gas + 1))
            P08 = P07 / crit_press_noz_core
            v8 = np.sqrt(kappa_gas * R * T08)
            rho8 = P08 / (R * T08)
            A8 = mdot_corefuel / (rho8 * v8)
            F_core = mdot_corefuel * (v8 - v_inf) + A8 * (P08 - Pa)
            v8eq = (F_core / mdot_core) + v_inf
        else:
            P08 = Pa
            T08 = T07 * (1 + (1 / eta_nozzle) * ((P08 / P07) ** ((kappa_gas - 1) / kappa_gas) - 1))
            v8 = np.sqrt(2 * cp_gas * (T07 - T08))
            F_core = mdot_corefuel * (v8 - v_inf)
            v8eq = v8

        # Thrust
        F_N_cal = F_core + F_bypass  # N
        SFC = mdot_f / (F_N_cal / 1000)  # kg/s / kN

        out.append([SFC / 1000, mdot_f, T04, F_N_cal])

        diff = abs(F_N_req - F_N_cal)

        return diff

    res = minimize_scalar(min_func, bounds=(1000, 3000), method='bounded')
    # print('Exited with difference of: ' + str(abs(F_N_req - out[-1][-1])))
    # print('TIT: ' + str(res.x))

    return out[-1]


def center_of_gravity_x(mainwing_cog_x, horztail_cog_x, verttail_cog_x, fuselage_cog_x,
                        mainwing_wingbox_cog_x, tank1_cog_x, w_tank1, tank2_cog_x, w_tank2,
                        apu_cog_x, nosebox_cog_x, engine_cog_x, pylon_cog_x, pilot_cog_x,
                        firstclassseats_cog_x, economyseats_cog_x, cargocontainer_cog_x,
                        cargocontainer_vol, nlg_cog_x, n_firstclassseats_row,
                        n_economyseats_row, w_tank1_fuel, w_tank2_fuel):
    """
    Aircraft center of gravity analysis tool, calculates the x c.g. position.

    Parameters
    ----------
    X_cog_x : float
        The x c.g. position of the X component in [m] measured from the nose of the aircraft
    w_tank1 : float
        The weight of fuel in and structure f tank 1 in [kg]

    Returns
    -------
    aircraft_cog_x
        The aircraft's x c.g. position in [m] measured from the nose of the aircraft
    aircraft_weight
        The sum of the individual weight components used in determining the x c.g. position
    """

    # TODO: change docstring

    # Weight inputs taken from Figure 42.25 on page 581 of the book Aerodynamic Design of Transport
    # Aircraft by E. Obert, ISBN:978-1-58603-970-7 unless indicated otherwise
    w_mainwing = 8801  # [kg]
    w_fuselage = 8938  # [kg]
    w_horztail = 625  # [kg]
    w_verttail = 463  # [kg]
    w_landinggear = 2275  # [kg] includes both the nose and main landing gear
    w_pylons = 907  # [kg]
    w_engines = 6621  # [kg]
    w_bleedairsys = 249  # [kg]
    w_enginecontrols = 29  # [kg]
    w_fuelsys = 299  # [kg]
    w_apu = 223  # [kg]
    w_hydraulicgen = 547  # [kg]
    w_hydraulicdist = 319  # [kg]
    w_aircon = 664  # [kg]
    w_autopilot = 101  # [kg]
    w_navsys = 415  # [kg]
    w_comms = 186  # [kg]
    w_electricgen = 343  # [kg]
    w_electricdist = 1032  # [kg]
    w_flightcontrol = 772  # [kg]
    w_person = 90  # [kg]
    w_seat_pilot = 60  # [kg]
    w_seat_firstclass = 10  # [kg]
    w_seat_economy = 11  # [kg] https://www.flightglobal.com/new-lufthansa-seat-saves-nearly-30-in
    # -weight/97485.article
    w_cargocontainer = 274  # [kg] https://vrr.aero/products/akh-container/
    cargo_weight_density = 161  # [kg/m3] https://www.icao.int/Meetings/STA10/Documents
    # /Sta10_Wp005_en.pdf
    w_cargocontainer_payload = cargo_weight_density * cargocontainer_vol  # [kg]
    w_extra = 103 + 200 + 79 + 85 + 30 + 3215  # [kg]

    # List containing all the weights and locations of the components
    cog_lst = [[w_mainwing, mainwing_cog_x],
               [w_horztail, horztail_cog_x],
               [w_verttail, verttail_cog_x],
               [w_fuselage, fuselage_cog_x],
               [w_bleedairsys, mainwing_wingbox_cog_x],
               [0.85 * w_landinggear, mainwing_wingbox_cog_x],  # MLG weight taken from Torenbeek
               [0.15 * w_landinggear, nlg_cog_x],  # NLG weight taken from Torenbeek
               [w_fuelsys, mainwing_wingbox_cog_x],
               [w_hydraulicgen + w_hydraulicdist, mainwing_wingbox_cog_x],
               [w_aircon, mainwing_wingbox_cog_x],
               [w_apu, apu_cog_x],
               [w_navsys, nosebox_cog_x],
               [w_comms, nosebox_cog_x],
               [w_flightcontrol, nosebox_cog_x],
               [w_electricgen, nosebox_cog_x],
               [w_electricdist, nosebox_cog_x],
               [w_autopilot, nosebox_cog_x],
               [w_engines, engine_cog_x],
               [w_pylons, pylon_cog_x],
               [w_tank1 + w_tank1_fuel, tank1_cog_x],
               [w_tank2 + w_tank2_fuel, tank2_cog_x],
               [2 * (w_person + w_seat_pilot), pilot_cog_x]
               ]

    # Adding the first class seats and passengers to cog_lst
    for j in np.arange(len(firstclassseats_cog_x)):
        cog_lst.append([n_firstclassseats_row * (w_person + w_seat_firstclass),
                        firstclassseats_cog_x[j]])

    # Adding the economy class seats and passengers to cog_lst
    for k in np.arange(len(economyseats_cog_x)):
        cog_lst.append([n_economyseats_row * (w_person + w_seat_economy), economyseats_cog_x[k]])

    # Adding the cargo containers to cog_lst
    for m in np.arange(len(cargocontainer_cog_x)):
        cog_lst.append([w_cargocontainer + w_cargocontainer_payload, cargocontainer_cog_x[m]])

    # Calculating the x c.g. position
    moment = 0
    aircraft_weight = 0
    for i in range(len(cog_lst)):
        moment = moment + (cog_lst[i][0] * cog_lst[i][1])
        aircraft_weight = aircraft_weight + cog_lst[i][0]

    aircraft_cog_x = moment / aircraft_weight

    w_OEM = aircraft_weight + w_enginecontrols + w_extra - \
            (w_tank1_fuel + w_tank2_fuel + w_person * (len(firstclassseats_cog_x) *
                                                       n_firstclassseats_row + len(
                        economyseats_cog_x) * n_economyseats_row) + len(cargocontainer_cog_x) *
             (w_cargocontainer + w_cargocontainer_payload))

    return [aircraft_cog_x, aircraft_weight, w_OEM]
