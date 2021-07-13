from kbeutils.geom import *

airfoil_code = '0015'

if len(airfoil_code) == 5:
    airfoil = naca_5_airfoil(designation=airfoil_code)
elif len(airfoil_code) == 4:
    airfoil = naca_4_airfoil(designation=airfoil_code)
else:
    print("Airfoil designation not found")

filename = 'NACA' + str(airfoil_code) + '.dat'

points_list = []
for i in range(len(airfoil)):
    points_list.append([round(airfoil[i][0], 5), round(airfoil[i][2], 5)])

print(points_list)

with open(filename, 'w') as output:
    for j in range(len(points_list)):
        my_str = str(points_list[j][0]) + ' ' + str(points_list[j][1])
        output.write(my_str + '\n')
