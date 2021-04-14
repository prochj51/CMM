from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits import mplot3d


class MplWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = Canvas(Figure())                  # Create canvas object
        self.canvas.axes = self.canvas.figure.gca(projection='3d')
        #self.canvas.axes.contour3D(X, Y, Z, 50, cmap='binary')
        
        
        self.vbl = QVBoxLayout()         # Set box for plotting
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

    def plot_scatter(self,X,Y,Z, id_m = "", op_name = ""):    
        self.canvas.axes.scatter3D(X,Y,Z)
        title = str(id_m) + ', ' + op_name
        self.canvas.axes.set_title(title)
        self.canvas.axes.set_xlabel('x')
        self.canvas.axes.set_ylabel('y')
        self.canvas.axes.set_zlabel('z') 
        #self.canvas.axes.view_init(elev=90, azim=-90)
      