import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.interpolate import interp1d
import numpy as np
import math
from mpl_toolkits.mplot3d import Axes3D


#***********
#Linear
#***********
#compensation on fly for linear edge
def compensate_linear(point0,point1,dir = 'XY'):
    if dir == 'XY':
        pt0 = point0
        pt1 = point1
    elif dir == 'YX':
        pt0 = list(reversed(point0))
        pt1 = list(reversed(point1))
    
    dx = pt1[0] - pt0[0]
    dy = pt1[1] - pt0[1]
    print("difs:",dx,dy)
    try:
        alpha = self.get_angle(dx,dy)
    except ZeroDivisionError:
        return None

    print("alpha:",alpha)

    alpha2 = math.pi/2 - alpha
    print("alpha2:",alpha2)
    
    phi = math.pi - math.pi/2 - alpha2
    print("phi:",phi)
    r = self.probe_tip_diam/2
    print(r)
    x_comp = r * math.sin(phi)
    y_comp = x_comp / math.tan(alpha2)    
    print("comp",x_comp,y_comp)

    if dir == 'XY':
        return x_comp,y_comp
    elif dir == 'YX':
        return y_comp,x_comp

#***************
#Cubic
#***************

def compensate_xy(x_values, y_values, reverse_list,comp):
    f_list = []
    dx = 0.01
    k = -1
    x_new = []
    y_new = []
    for i,(x,y,rev) in enumerate(zip(x_list,y_list,reverse_list)):
        plt.scatter(x,y)
        if rev:
            x,y = reverse(x,y)

        f = interp1d(x, y, kind='cubic')
        f_list.append(f)
        
        for x_i in x:
            x0 = x_i
            x1 = x_i + dx
            y0 = f(x0)
            try:
                y1 = f(x1)
                dy = y1-y0     
            except ValueError: #when we are out of range
                dx = -dx
                continue
                # x1= x0+dx
                # y1 = f(x1)
                # dy = y0-y1
                
            dy = 0 if abs(dy) < 0.0001 else dy
            if reverse:
                n = np.array([-dy,dx])
            else:
                n = np.array([dy,-dx])

            n = k*n/math.sqrt(dy**2+dx**2)
            
            if rev:
                #y is real x and vice versa
                x0, y0 = reverse(x0,y0)
                n = n[::-1]

            x_c = x0+n[0]
            y_c = y0+n[1]
            x_new.append(x_c)
            y_new.append(y_c)

            #plt.plot(x0+n[0], y0+n[1], marker = '.',c='r')

    return x_new, y_new, f_list

#***************
#Gradient
#***************

def compensate_xyz(X,Y,Z, comp):
    X_new = np.copy(X)
    Y_new = np.copy(Y)
    Z_new = np.copy(Z)
    gradx,grady = np.gradient(Z)
    for row_indx in range(0,len(gradx)):
        for col_indx in range(0,len(gradx[0])):
            n = np.array([gradx[row_indx][col_indx],grady[row_indx][col_indx],-1])
            v = np.linalg.norm(n)
            n = comp*n/v
            
            X_new[row_indx][col_indx] = X[row_indx][col_indx] + n[0]
            Y_new[row_indx][col_indx] = Y[row_indx][col_indx] + n[1]
            Z_new[row_indx][col_indx] = Z[row_indx][col_indx] + n[2]
    return X_new, Y_new, Z_new


#Test data.
# X = np.arange(-5, 5, 0.5)

# Y = np.arange(-5, 5, 0.5)
# X, Y = np.meshgrid(X, Y)
# R = np.sqrt(X**2 + Y**2)
# Z = np.sin(R)


# x,y,z = compensate_xyz(X,Y,Z, 1.5)

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.plot_surface(X,Y,Z)
# ax.scatter(x,y,z)
# plt.show()

Z = np.array([0,0,1,1])
res = np.gradient(Z,1)
print(res)