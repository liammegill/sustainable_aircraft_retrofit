from parapy.core import Input, Attribute, action
from parapy.geom import GeomBase
from parapy.core.validate import *
import xml.etree.ElementTree as ET
import subprocess, xmltodict
import numpy as np
import math as m
from hydrogen_aircraft import aircraft_data, isa_calculator, aero_engine_code, ENGINE_DIR
import os
from datetime import *


# define required functions (outside of parapy class)
def update_design_parameter(engine_data_dict, parameter, parameter_id, component_id):
    """
    Update design parameter in GSP 11 save file.

    Parameters
    ----------
    engine_data_dict : dict
        Data from GSP xml save file stored as an orderedDict.
    parameter : float
        Parameter value to be added to save file.
    parameter_id : str
        GSP name of the parameter. For examples, see the gsp_lookup dictionary.
    component_id : str
        GSP name of the relevant component. For examples, see the gsp_lookup dictionary.

    Returns
    -------
    engine_data_dict: collections.OrderedDict
        Updated input dictionary

    """

    # define temporary dictionary of data
    temp_dict = engine_data_dict['Project']['ReferenceModel']['Components']['TGSPcomp']

    # find component and parameter corresponding to input, then replace
    components_id_list = [i['@ID'] for i in temp_dict]
    component_index = components_id_list.index(component_id)
    parameters_id_list = [i['@ID'] for i in temp_dict[component_index]['CompForm']['INumFld']]
    parameter_index = parameters_id_list.index(parameter_id)
    temp_dict[component_index]['CompForm']['INumFld'][parameter_index]['Value'] = str(parameter)

    # replace the relevant part of the engine_data_dict with the new temporary dict
    engine_data_dict['Project']['ReferenceModel']['Components']['TGSPcomp'] = temp_dict
    return engine_data_dict


def update_cruise_thrust(engine_data_dict, parameter, parameter_id, component_id,
                         config):
    """
    Update cruise thrust value in GSP 11 save file.

    Parameters
    ----------
    engine_data_dict : dict
        Data from GSP xml save file stored as an orderedDict.
    parameter : float
        Parameter value to be added to save file.
    parameter_id : str
        GSP name of the parameter. For examples, see the gsp_lookup dictionary.
    component_id : str
        GSP name of the relevant component. For examples, see the gsp_lookup dictionary.
    config : str
        Name of configuration in GSP 11. Currently, choice of 'Config_1' and 'Config_2'. See GSP
        save file for more details

    Returns
    -------
    engine_data_dict: collections.OrderedDict
        Updated input dictionary

    """

    # find relevant configuration and define temp_dict of the values
    config_id_list = [i['@ID'] for i in engine_data_dict['Project']['ReferenceModel']['Config']]
    # TODO: check how many cases there are and act accordingly
    temp_dict = engine_data_dict['Project']['ReferenceModel']['Config'][
        config_id_list.index(config)]['Components']['TGSPcomp']

    # find component and parameter corresponding to input, then replace
    components_id_list = [i['@ID'] for i in temp_dict]
    component_index = components_id_list.index(component_id)
    parameters_id_list = [i['@ID'] for i in temp_dict[
        component_index]['CompForm']['INumFld']]
    parameter_index = parameters_id_list.index(parameter_id)
    temp_dict[component_index]['CompForm']['INumFld'][parameter_index]['Value'] = str(parameter)

    # replace the relevant part of the engine_data_dict with the new temporary dict
    engine_data_dict['Project']['ReferenceModel']['Config'][
        config_id_list.index(config)]['Components']['TGSPcomp'] = temp_dict
    return engine_data_dict


def update_cruise_conditions(engine_data_dict, altitude, mach, config):
    """
    Update ambient conditions for cruise.

    Parameters
    ----------
    engine_data_dict : dict
        Data from GSP xml save file stored as an orderedDict.
    altitude : float
        Cruise altitude [m]
    mach : float
        Cruise Mach number
    config : str
        Name of configuration in GSP 11. Currently, choice of 'Config_1' and 'Config_2'. See GSP
        save file for more details

    Returns
    -------
    engine_data_dict: collections.OrderedDict
        Updated input dictionary

    """

    # navigate to correct ambient conditions and define temp_dict
    config_id_list = [i['@ID'] for i in engine_data_dict['Project']['ReferenceModel']['Config']]
    temp_dict = engine_data_dict['Project']['ReferenceModel']['Config'][
        config_id_list.index(config)]['Case']['AmbConditions']['INumFld']

    # calculate ambient conditions and save in a dictionary
    Ts, Ps, rho = isa_calculator(altitude)
    Tt = Ts * (1 + 0.4 / 2 * mach ** 2)
    Pt = Ps * (Tt / Ts) ** (1.4 / 0.4)
    Zp = altitude
    Vt = mach * m.sqrt(1.4 * 287 * Ts)
    conditions = {'Ts': Ts, 'Ps': Ps, 'rho': rho, 'Tt': Tt, 'Pt': Pt, 'Zp': Zp, 'Vt': Vt}

    # replace values and return new dictionary
    parameter_id_list = [i['@ID'] for i in temp_dict]
    for parameter in conditions.keys():
        temp_dict[parameter_id_list.index(parameter)]['Value'] = str(conditions[parameter])
    engine_data_dict['Project']['ReferenceModel']['Config'][
        config_id_list.index(config)]['Case']['AmbConditions']['INumFld'] = temp_dict
    return engine_data_dict


# lookup dictionary with relevant design parameters
# TODO add all other parameters to GSP load
gsp_designpar_lookup = {'inlet_mdot_takeoff': {'gsp_id': 'Wdes',
                                               'component_id': 'Inlet'},
                        'fan_core_pressure_ratio': {'gsp_id': 'PRdescore',
                                                    'component_id': 'Fan'},
                        'fan_duct_pressure_ratio': {'gsp_id': 'PRdesduct',
                                                    'component_id': 'Fan'},
                        'bypass_ratio': {'gsp_id': 'BPRdes',
                                         'component_id': 'Fan'},
                        'fan_core_eta': {'gsp_id': 'ETAdes',
                                         'component_id': 'Fan'},
                        'fan_duct_eta': {'gsp_id': 'ETAdesduct',
                                         'component_id': 'Fan'},
                        'lpc_pressure_ratio': {'gsp_id': 'PRdes',
                                               'component_id': 'Booster'},
                        'lpc_eta': {'gsp_id': 'ETAdes',
                                    'component_id': 'Booster'},
                        'hpc_pressure_ratio': {'gsp_id': 'PRdes',
                                               'component_id': 'HPC'},
                        'hpc_eta': {'gsp_id': 'ETAdes',
                                    'component_id': 'HPC'},
                        'cc_max_exit_temperature': {'gsp_id': 'Texitdes',
                                                    'component_id': 'Combustor'},
                        'manual_fuel_control_temp': {'gsp_id': 'Input1',
                                                     'component_id': 'Manual Fuel Control'}
                        }


# ParaPy class
class Turbofan(GeomBase):
    """
    KBE Assignment 2021: Hydrogen Retrofitted Aircraft

    Class: Turbofan

    Authors: Liam Megill & Tom Hoogerdijk

    Date: Sunday 18th April 2021

    Defines a simplified hydrogen turbofan. Currently, no geometry is created by this class.
    Instead, a set of actions are available for the user to analyse the aircraft performance at
    take-off, climb and cruise. Both simplified aero engine code functions and GSP 11 analysis
    functions are provided. All values default to the Airbus A320 CFM56B engine.
    """

    # General aircraft inputs (all passed down). Private if not run as main file.
    baseline_aircraft = Input('A320', private=not (__name__ == '__main__'),
                              validator=OneOf(['A320']))
    maximum_takeoff_mass = Input(70000, private=not (__name__ == '__main__'))  # [kg]
    cruise_altitude = Input(12910, private=not (__name__ == '__main__'))  # [m]
    cruise_mach_number = Input(0.78, private=not (__name__ == '__main__'))  # [-]
    total_cruise_thrust = Input(13000, private=not (__name__ == '__main__'))  # [N]

    @Attribute  # for single engine!
    def cruise_thrust(self):
        return self.total_cruise_thrust / self.n_engines

    n_engines = Input(2, private=not (__name__ == '__main__'))  # [-]
    planform_area = Input(123, private=not (__name__ == '__main__'))  # [m2]
    aspect_ratio = Input(9.5, private=not (__name__ == '__main__'))  # [-]
    oswald_efficiency = Input(0.8, private=not (__name__ == '__main__'))  # [-]
    zero_lift_drag_coefficient = Input(0.018, private=not (__name__ == '__main__'))  # [-]


    # Turbofan inputs
    fan_diameter = Input(1.73)  # [m]
    inlet_mdot_takeoff = Input(408, validator=Positive())  # [kg/s] design value

    @Attribute
    def inlet_mdot_cruise(self):
        """ Estimates corrected mass flow through the inlet of the engine in cruise conditions."""
        [T, _, rho] = isa_calculator(self.cruise_altitude)
        v_inf = self.cruise_mach_number * np.sqrt(1.4 * 287 * T)
        fan_area = np.pi * (self.fan_diameter / 2) ** 2
        return v_inf * fan_area * rho

    bypass_ratio = Input(11.0, validator=Positive())
    fan_core_pressure_ratio = Input(1.25, validator=Range(1, 1.4))
    fan_core_eta = Input(0.93, validator=Range(0, 1))

    @Attribute  # assume duct and core pressure ratios and efficiencies are equivalent
    def fan_duct_pressure_ratio(self):
        return self.fan_core_pressure_ratio

    @Attribute
    def fan_duct_eta(self):
        return self.fan_core_eta

    lpc_pressure_ratio = Input(1.7, validator=GreaterThan(1))
    lpc_eta = Input(0.91, validator=Range(0, 1))
    hpc_pressure_ratio = Input(10.0, validator=GreaterThan(1))
    hpc_eta = Input(0.84, validator=Range(0, 1))
    cc_max_exit_temperature = Input(1800, validator=Positive())

    @Attribute
    def manual_fuel_control_temp(self):
        return self.cc_max_exit_temperature

    # gsp paths
    gsp_savefile_path = Input('H2_turbofan_LEAP1A.xml')
    gsp_updated_path = Input('output/hydrogen_turbofan_kbe.xml')
    gsp_link = Input('C:\\Program Files (x86)\\NLR\\GSP\\GSP.exe')

    # simplified aero engine code
    @Attribute(private=True)
    def aero_engine_calculations(self):
        return aero_engine_code(mach=self.cruise_mach_number,
                                altitude=self.cruise_altitude,
                                lhv=120.0,
                                thrust=self.cruise_thrust,
                                max_T04=self.cc_max_exit_temperature,
                                mdot_cor=self.inlet_mdot_cruise,
                                BPR=self.bypass_ratio,
                                Pr_inlet=1.0,
                                Pr_fan=self.fan_core_pressure_ratio,
                                Pr_LPC=self.lpc_pressure_ratio,
                                Pr_HPC=self.hpc_pressure_ratio,
                                Pr_comb=0.96,
                                isen_fan=self.fan_core_eta,
                                isen_lpc=self.lpc_eta,
                                isen_hpc=self.hpc_eta,
                                isen_lpt=0.92,
                                isen_hpt=0.92,
                                eta_mech=0.99,
                                eta_comb=0.995,
                                eta_nozzle=0.98)

    # these values are inputs because they can be overwritten by the user after running GSP 11
    @Input
    def tsfc_cal(self):  # [kg/Ns]
        return self.aero_engine_calculations[0]

    @Input
    def mdot_f_cal(self):
        return self.aero_engine_calculations[1]

    @Input
    def T04_cal(self):
        return self.aero_engine_calculations[2]

    # GSP 11 functions
    @action
    def gsp_analysis(self):
        """ Update GSP xml save file with new values and load GSP 11.
        """
        path = os.path.join(ENGINE_DIR, self.gsp_savefile_path)
        data: dict = xmltodict.parse(ET.tostring(ET.parse(path).getroot()))
        for key in gsp_designpar_lookup:
            data = update_design_parameter(data, eval('self.' + key),
                                           gsp_designpar_lookup[key]['gsp_id'],
                                           gsp_designpar_lookup[key]['component_id'])
        data = update_cruise_thrust(data, self.cruise_thrust,
                                    'Input1', 'Thrust Control', 'Config_2')
        data = update_cruise_conditions(data, self.cruise_altitude, self.cruise_mach_number,
                                        'Config_2')
        with open(self.gsp_updated_path, 'w') as result_file:
            result_file.write(xmltodict.unparse(data))
        subprocess.Popen("%s %s" % (self.gsp_link, self.gsp_updated_path))
        return

    @action
    def create_climb_rate_diagram(self):
        """ Creates climb rate vs altitude diagram. The user is asked whether an existing climb
        thrust profile from GSP is already available, else gsp_analysis is called, which opens
        GSP 11. The user can then run climb_case within GSP 11 and save a report made from the
        output table as a txt file. This file can be selected by the pop-up menu in ParaPy,
        which is used to create the climb rate diagram.

        """

        from tkinter import Tk, messagebox
        from tkinter.filedialog import askopenfilename
        import matplotlib
        matplotlib.use('TKAgg')
        import matplotlib.pyplot as plt
        # import matplotlib
        # matplotlib.use('Qt5Agg')

        # Ask user whether applicable report from GSP already exists
        Tk().withdraw()
        user_response = messagebox.askyesnocancel("Check for up-to-date engine data",
                                                  "To calculate the climb rate, GSP 11 data for"
                                                  "the selected engine is required. If this data"
                                                  "is already stored, choose 'Yes'. Choose 'No' to"
                                                  " open GSP 11 to create the data. Choose "
                                                  "'cancel' to exit.")

        # if report does not exist, modify save file and open GSP 11
        if not user_response:
            self.gsp_analysis()
            messagebox.showinfo('GSP 11 Instructions',
                                "Please follow these instructions in GSP 11: \n"
                                "1. Select and run the climb_case (F9) and choose 0.0 in the "
                                "pop-up window; \n"
                                "2. Save output table as a report; \n"
                                "3. Save report as a .txt file in local folder. "
                                "4. Choose this .txt file in the GUI pop-up shown after clicking "
                                "okay in this window.")

        # if cancel is clicked, return
        elif user_response is None:
            return

        # ask user for path to GSP report. Only txt files allowed to prevent accidents
        gsp_datafile_path = askopenfilename(title='Choose GSP report',
                                            filetypes=[('Text files', '.txt')])

        # if cancel is clicked, return
        if gsp_datafile_path == '':
            return

        # open report file and calculate climb rate
        gsp_data_file = open(gsp_datafile_path, 'r')
        lines = gsp_data_file.readlines()
        gsp_data_file.close()
        del lines[-1]
        new_gsp_file = open('output/gsp_StSt_edited.txt', 'w')
        for line in lines:
            new_gsp_file.write(line)
        new_gsp_file.close()
        data = np.loadtxt('output/gsp_StSt_edited.txt', skiprows=8)
        altitudes = data[:, 1] / 0.3048
        densities = data[:, 2]
        speeds = data[:, 4]
        thrusts = 2 * data[:, 5] * 1000
        powers = speeds * thrusts  # power = thrust * speed
        drag = self.zero_lift_drag_coefficient * 0.5 * densities * speeds ** 2 * \
               self.planform_area + 2 * (self.maximum_takeoff_mass * 9.81) ** 2 / \
               (np.pi * self.aspect_ratio * self.oswald_efficiency * densities * speeds ** 2 *
                self.planform_area)
        climb_rate = (powers - drag * speeds) / (self.maximum_takeoff_mass * 9.81) / 0.3048 * 60

        # plot climb rate of aircraft
        fig, ax = plt.subplots()
        ax.plot(altitudes, climb_rate, color='tab:blue', label='Current aircraft', marker='o')

        # plot comparison aircraft data
        comparison_rate_lst = ['climb_rate_high', 'climb_rate_nom']
        label_lst = ['73.5t', '62.0t']
        marker_lst = ['^', 'p']
        for climb_rate, label, marker in zip(comparison_rate_lst, label_lst, marker_lst):
            ax.plot(aircraft_data[self.baseline_aircraft]['climb_rate_hts'],
                    aircraft_data[self.baseline_aircraft][climb_rate],
                    label=self.baseline_aircraft + ' ' + label, marker=marker, color='tab:red')
        ax.set(xlabel='Altitude [ft]', ylabel='Climb rate [ft/min]')
        ax.set_ylim([0, None])
        ax.legend(loc='best')
        fig.tight_layout()

        # Save plot to output folder
        from tkinter import Tk, messagebox
        Tk().withdraw()
        user_response = messagebox.askyesno('Save diagram',
                                            'Do you want to save the climb rate diagram?')
        if user_response:
            DIR_output = os.getcwd() + '\\output\\'
            filename_num = '_{date:%Y-%m-%d_%H%M%S}'.format(date=datetime.now())
            fname = DIR_output + 'Airbus_A320_climb_rate_diagram' + filename_num + '.pdf'
            plt.savefig(fname)

        plt.show()

# open if used as main file
if __name__ == '__main__':
    from parapy.gui import display

    obj = Turbofan()
    display(obj)
