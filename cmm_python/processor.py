import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.interpolate import interp1d
import numpy as np
import math
from mpl_toolkits.mplot3d import Axes3D


def reverse(x,y):
    tmp = x
    x = y
    y = tmp
    return x, y

def vec_size(vec):
    return math.sqrt(vec[0]**2 + vec[1]**2) 
def dot_product(vec_1, vec_2):
    return vec_1[0]*vec_2[0] + vec_1[1]*vec_2[1]        

def get_angle(pt0, pt1):
    dx = pt1[0] - pt0[0]
    dy = pt1[1] - pt0[1]
    return math.atan(float(dy)/float(dx))

def get_absolute_angle(pt0, pt1):
    dx = pt1[0] - pt0[0]
    dy = pt1[1] - pt0[1]
    vec1 = [pt0[0],0]
    vec2 = [dx,dy]
    if pt1[1] < pt0[1]:
        sign = -1
    else:
        sign = 1
    return sign*math.acos(dot_product(vec1,vec2)/(vec_size(vec1) * vec_size(vec2)))
    
def get_normal_vector(pt0, pt1):
    dx = pt1[0] - pt0[0]
    dy = pt1[1] - pt0[1]
    n = np.array([dy,-dx])
    return n/vec_size(n)
    
def get_line_coeff(pt0, pt1):
    k = float(pt1[1] - pt0[1])/float(pt1[0] - pt0[0])    
    q = pt0[1] - k * pt0[0]
    return k, q 

#***********
#Linear
#***********
#compensation on fly for linear edge
def compensate_linear(point0,point1,radius,dir = 'xplus'):
    
    if dir == 'yplus' or dir == 'yminus':
        pt0 = point0
        pt1 = point1
    elif dir == 'xplus' or dir == 'xminus':
        pt0 = list(reversed(point0))
        pt1 = list(reversed(point1))
    try:
        alpha = get_angle(pt0,pt1)
    except ZeroDivisionError:
        return None

    alpha2 = math.pi/2 - alpha
    #print(alpha2)
    #old
    # phi = math.pi - math.pi/2 - alpha2
    # r = comp/2
    # x_comp = r * math.sin(phi)
    # y_comp = x_comp / math.tan(alpha2)    

    #new
    if dir == 'yminus' or dir == 'xminus':
        sign_y = -1
        sign_x = 1
    else:
        sign_y = 1
        sign_x  = -1
  
    x_comp = sign_x * radius * math.cos(alpha2)
    y_comp = sign_y*radius * math.sin(alpha2)

    if dir == 'yplus' or dir == 'yminus':
        return x_comp,y_comp
    elif dir == 'xplus' or dir == 'xminus':
        return y_comp,x_comp

def compensate_xy_linear(x, y, comp):  
    x_new = []
    y_new = []
    for indx in range(0,len(x)):
        next = indx + 1
        if next < len(x):
            pt0 = [x[indx], y[indx]]
            pt1 = [x[next], y[next]]
        n = get_normal_vector(pt0,pt1)
        
        x_new.append(x[indx] +comp*n[0])
        y_new.append(y[indx] + comp*n[1])

    return x_new, y_new


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

def main():
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

    # Z = np.array([0,0,1,1])
    # res = np.gradient(Z,1)
    # print(res)
    #print(compensate_linear([10,10],[15,12],1.5,"yminus"))
    


if __name__ == "__main__":
    main()