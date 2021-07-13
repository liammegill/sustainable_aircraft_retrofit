import os

DIR = os.path.dirname(__file__) + '/output/'


def write_output_txt_file(aircraft, filename, output_list, aero_analysis,
                          avl_results, cl_cd, cg_mac, cg_analysis, r_ferry, r_maxpayload):
    """
    Exports most important attributes and the results from the external analysis modules of the
    current instance to a .txt file

    Parameters
    ----------
    aircraft : str
        name of baseline aircraft
    filename : str
        name of file with date and time stamp
    output_list : list
        list of attribute names, attribute values and attribute units to be outputted to .txt file
    aero_analysis : list
        list of results from aero engine analysis
    avl_results : list
        list of results from AVL analysis
    cl_cd : float
        lift to drag ratio calculated from AVL analysis [-]
    cg_mac : float
        the center of gravity x position wrt to the MAC [%]
    cg_analysis : list
        list of results from c.g. analysis
    r_ferry : float
        ferry range [m]
    r_maxpayload : float
        max payload range [m]
    """
    with open(filename + '.txt', "w") as f:
        str_header = 'Hydrogen Retrofit Design Report'
        str_second = 'Baseline Aircraft: Airbus ' + aircraft
        str_third = 'Instance: ' + filename[-17:]
        f.writelines(
            '==========================================================\n'
            + str_header + '\n' + str_second + '\n' + str_third +
            '\n----------------------------------------------------------\n' + 'Main Results ('
                                                                               'int. analysis)\n')

        for i in range(len(output_list)):
            f.writelines(f"{str(output_list[i][0]).ljust(27)}"
                         f"{str(output_list[i][1]).ljust(23)}"
                         f"{output_list[i][2]}\n")

        f.writelines('----------------------------------------------------------\n')
        f.writelines('Range Calculation Results (ext. analysis)\n')
        f.writelines(f"{'Max. payload range'.ljust(26)} {str(r_maxpayload).ljust(22)} [m]\n")
        f.writelines(f"{'Ferry range'.ljust(26)} {str(r_ferry).ljust(22)} [m]\n")

        f.writelines('----------------------------------------------------------\n')
        f.writelines('AVL Results (ext. analysis)\n')
        f.writelines(f"{'CL/CD'.ljust(26)} {str(cl_cd).ljust(22)} [-]\n")
        f.writelines(f"{'Alpha_cruise'.ljust(26)} "
                     f"{str(avl_results['Totals']['Alpha']).ljust(22)} [deg]\n")
        f.writelines(f"{'CL_tot'.ljust(26)} {str(avl_results['Totals']['CLtot']).ljust(22)} [-]\n")
        f.writelines(f"{'CD_tot'.ljust(26)} {str(avl_results['Totals']['CDtot']).ljust(22)} [-]\n")
        f.writelines(f"{'CD_ind'.ljust(26)} {str(avl_results['Totals']['CDind']).ljust(22)} [-]\n")
        f.writelines(f"{'CD_0'.ljust(26)} {str(avl_results['Totals']['CDvis']).ljust(22)} [-]\n")
        f.writelines(f"{'MAC'.ljust(26)} {str(avl_results['Totals']['Cref']).ljust(22)} [m]\n")
        f.writelines(f"{'Planform Area'.ljust(26)}"
                     f" {str(avl_results['Totals']['Sref']).ljust(22)} [m2]\n")
        f.writelines(f"{'Oswald efficiency factor'.ljust(26)}"
                     f" {str(avl_results['Totals']['e']).ljust(22)} [-]\n")

        f.writelines('----------------------------------------------------------\n')
        f.writelines('C.G. Analysis Results (ext. analysis)\n')
        f.writelines(f"{'C.G. position'.ljust(26)} {str(cg_mac).ljust(22)} [%]\n")
        f.writelines(f"{'Operating Empty Mass'.ljust(26)} {str(cg_analysis[2]).ljust(22)} [kg]\n")

        f.writelines('----------------------------------------------------------\n')
        f.writelines('Aero Engine Calculation Results (ext. analysis)\n')
        f.writelines(f"{'tsfc_cal'.ljust(26)} {str(aero_analysis[0]).ljust(22)} [kg/Ns]\n")
        f.writelines(f"{'mdot_f_cal'.ljust(26)} {str(aero_analysis[1]).ljust(22)} [kg/s]\n")
        f.writelines('==========================================================')
