# AE4204 KBE Assignment 2021: Hydrogen retrofit of single-aisle aircraft

**Authors:** Liam Megill & Tom Hoogerdijk

**Summary:** With aviation currently responsible for over 5% of anthropogenic warming, new, 
climate-friendly aircraft are required to reduce the industry's emissions. One promising 
solution is the use of liquid hydrogen (LH<sub>2</sub>), either for use in hydrogen fuel cells 
or for combustion in modified turbofan engines. According to the latest studies ([Hydrogen-powered 
Aviation Report, May 2020](https://www.fch.europa.eu/sites/default/files/FCH%20Docs/20200720_Hydrogen%20Powered%20Aviation%20report_FINAL%20web.pdf)), hydrogen is most cost-effective for short- to medium-range 
aircraft in the near future. This application endeavours to explore the possibility of hydrogen 
combustion in retrofitted single-aisle short- or medium-range aircraft such as the Airbus A320. 
The hydrogen is stored in liquid form in fuel tanks at the rear of the aircraft, which reduces 
space used for passenger seating in today's aircraft. Using this application, the user is thus 
able to visualise the design changes and trade-offs between the number of passengers and 
achieved range with a limited internal volume.

**Usage:**

The complete aircraft model can be loaded by running `main.py`. A pop-up window will 
ask whether the user wants to load a previously saved model or whether the user would like to 
start from the default Airbus A320. A number of single-aisle aircraft (e.g. A318) are 
provided and can be loaded as a previously saved model. To load a previously saved model 
navigate to the `.json` file through the file dialog window. By selecting 'no', the `input.txt` 
file will be loaded. The `input.txt` file defines the passenger seating configuration including 
the number of rows and number of classes and can be modified before running `main.py`. 

Once the GUI has opened, the user can modify the inputs in the property view and visualise the 
corresponding changes to the aircraft in the geometry view. For example the length of the 
fuselage, the number of LH<sub>2</sub> tanks and the seating configuration can all be modified. 
Any modification to these inputs will alter the internal cabin layout based on the rule-based 
parametric model. For example increasing the number of seat rows will reduce the size of the 
LH<sub>2</sub> tanks. On the port side of the aircraft the c.g. position is visualised. The red 
sphere visualises the x c.g. position and the yellow rod visualises the mean aerodynamic chord.
