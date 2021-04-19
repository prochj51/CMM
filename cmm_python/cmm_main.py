import cv2
from cmm import Ui_MainWindow

from PyQt5 import QtWidgets, QtCore
# from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
# from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
# from PyQt5.QtGui import QImage, QPixmap

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from enum import Enum
import imageHandler
import linuxcnc_driver 
from linuxcnc_driver import AbortException
import common
from database import CmmDb, CmmDatalog
import time
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class State(Enum):
    CalibrateCamera = 1
    GetParams = 5
    SelectOrigin = 7
    CameraReady = 8
    Move = 9
    Reference_Z = 10
    Draw = 15
    SelectPoints = 20

class Thread(QThread):
    state = State.CalibrateCamera
    changePixmap = pyqtSignal(QImage)
    win = None
    key = 255
    def run(self):
        video_capture = imageHandler.camera_setup()    
                          
        while True:
            
            if not imageHandler.updateImage.pause_updates:
                orig_img = cv2.cvtColor(imageHandler.next_frame2(video_capture), cv2.COLOR_BGR2RGB)
                imageHandler.updateImage.last_image0 = orig_img
            else:
                orig_img = imageHandler.updateImage.last_image0
            
            if self.win is None:
                continue
    
            #self.win.update()
            
            if True:
                # https://stackoverflow.com/a/55468544/6622587
                #rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #cv2.namedWindow('test draw')
                #cv2.setMouseCallback('test draw',click_and_crop)
                if self.key is not 255:
                    self.win.process_key(self.key)
                    self.key = 255
                
                imageHandler.check_layers(orig_img)
                
                if self.win.state == State.CalibrateCamera:
                    self.win.ui.instructionLabel.setText("Select base plate points")
                    if imageHandler.warpImage():
                        self.win.state = State.GetParams
                        self.win.ui.instructionLabel.setText("Enter dimensions of base plate")
                
                elif self.win.state == State.SelectOrigin:
                    self.win.ui.instructionLabel.setText("Select [0,0] origin")
                    if len(imageHandler.points_struct) != 0:
                        imageHandler.setOrigin() 
                        self.win.set_camera_scale()
                        self.win.state = State.SelectPoints
                        self.win.ui.instructionLabel.setText("Machine is ready")
                

                elif self.win.state == State.SelectPoints or \
                self.win.state == State.Draw:
                    pix_x, pix_y = self.win.driver.cnc_to_camera(self.win.x_act,self.win.y_act)
                    imageHandler.actual_position = [pix_x, pix_y]
                # elif  self.win.state == State.CameraReady:
                #     self.win.state = State.Move #temporary  
                # 
                # elif self.win.state == State.Draw:
                #     pass
                
                # elif self.win.state == State.SelectPoints:
                #     self.win.ui.instructionLabel.setText("Select point for Z reference a hit reference Z")
                
                # elif self.win.state == State.Reference_Z:
                #     self.win.ui.instructionLabel.setText("Select point for Z reference a hit reference Z")
                    

                # elif self.win.state == State.Move:
                #     self.win.ui.instructionLabel.setText("Select point for probing")
                    
                            
                
                final_pic = imageHandler.updateImage(orig_img)
                # mask = imageHandler.plate_mask(final_pic)
                # gray = cv2.cvtColor(cv2.bitwise_and(mask, final_pic), cv2.COLOR_BGR2GRAY)
                # final_pic /= 2
                # final_pic[cv2.bitwise_not(mask) == 255] /= 2
                common.draw_fps(final_pic)
                h, w, ch = final_pic.shape
                #print(rgbImage.shape)
                bytesPerLine = ch * w
                convertToQtFormat = QImage(final_pic.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_up_dictionary()
        self.init_ui()
        self.state = State.CalibrateCamera
        self.driver = linuxcnc_driver.CncDriver(wait_func=self.wait)
        self.db = CmmDb()
        self.db.open()
        self.confirmed = False
        self.plot_id = ""
        self.plot_op_name = "" 


    @pyqtSlot(QImage)
    def set_image(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))   

    def init_ui(self):
        self.setWindowTitle("Win")
        #self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(1200, 800)
        # create a label
        self.label = self.ui.cvlabel
        self.label.move(280, 120)
        self.label.resize(640, 480)
        self.label.setMouseTracking(True)
        self.label.installEventFilter(self)
        self.ui.enterDimensionsButton.clicked.connect(self.process_dimensions)
        self.ui.moveButton.clicked.connect(self.update_plot)
        self.ui.referenceZ.clicked.connect(self.reference_z)
        self.ui.startButton.clicked.connect(self.start)
        self.ui.clearPointsButton.clicked.connect(self.clear_points)
        self.ui.confirmButton.clicked.connect(self.confirm)
        self.ui.abortButton.clicked.connect(self.abort_action)
        self.init_combo_box()
        self.selectedPoints = []
        self.th = Thread(self)
        self.th.changePixmap.connect(self.set_image)
        self.th.start()
        #CNC Update
        timer1 = QTimer(self)
        timer1.timeout.connect(self.update_cnc)
        timer1.start(50)
        #Plot update
        timer2 = QTimer(self)
        timer2.timeout.connect(self.update_plot)
        timer2.start(200)
        self.addToolBar(NavigationToolbar(self.ui.plotWidget.canvas,self))
        self.show()    

    def eventFilter(self, source, event):
        t = event.type()
        
        if t == QtCore.QEvent.MouseMove or t== QtCore.QEvent.MouseButtonPress or t== QtCore.QEvent.MouseButtonRelease :
            if self.state == State.Draw:
                imageHandler.object_drawing_qt(event,event.x(), event.y())
            else:
                imageHandler.click(event,event.x(), event.y())
        
        return super(MainWindow, self).eventFilter(source, event)

    def keyPressEvent(self, event):
        self.th.key = event.key()
        event.accept()

    def init_combo_box(self):
        for key in self.op_dictionary:
            self.ui.comboBox.addItem(key)    
                   

    def set_up_dictionary(self):
        self.op_dictionary = {

            "Find inner hole position" : self.find_position,
            "Find outer hole position" : self.find_position,
            "Find inner rectangle position" : self.find_position,
            "Scan XY"  : self.scan_xy,
            "Scan circumference"   : self.scan_xy,
            "Circularity"   : self.scan_xy,
            "Cylindarity" :  self.scan_xy,
            "Straightness"  : self.scan_line
        }

    def process_dimensions(self):
        if self.state != State.GetParams:
            return
        try:
            self.calib_width = float(self.ui.widthInput.text())
            self.calib_height = float(self.ui.heightInput.text())
        except ValueError:
            self.ui.instructionLabel.setText("Wrong dimensions")
            return
        self.state = State.SelectOrigin
        
        #print(width)
        #print(height)
        # print(imageHandler.calib_rect_width)
        # print(imageHandler.calib_rect_height)
        # print(scale_x,scale_y)
    def set_camera_scale(self):
        origin = imageHandler.cnc_origin[0]
        scale_x = self.calib_width/imageHandler.updateImage.calib_rect_width
        scale_y = self.calib_height/imageHandler.updateImage.calib_rect_height
        x0 = origin[0]
        y0 = origin[1]
        self.driver.set_camera_scale(x0,y0,scale_x,scale_y)
        camera_home_x, camera_home_y =  self.driver.camera_to_cnc(imageHandler.updateImage.center_x,imageHandler.updateImage.center_y)
        self.driver.set_camera_home(camera_home_x,camera_home_y)

    def create_datalog(self,db, op_name):
        datalog = CmmDatalog(self.db)
        id_m = datalog.logMeasurement(op_name)
        self.plot_id = id_m
        self.plot_op_name = op_name
        return datalog

    def clear_points(self):
        imageHandler.points_struct = []
    
    def confirm(self):
        self.confirmed = True

    def start(self):
        func = self.ui.comboBox.currentText()
        self.confirmed = False
        self.driver.aborted = False
        self.op_dictionary[func](func)

    def wait(self,ms = 200):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec_()

    def update_plot(self):
        
        if self.db.change_status == False:
            return
        data = self.db.get_probed_values(self.db.last_meas_id)
        data = np.array(data)
        if data.size == 0:
            return
        print("Drawing data")
        x = data[:,0]
        y = data[:,1]
        z = data[:,2]
        
        self.ui.plotWidget.canvas.axes.clear()
        
        self.ui.plotWidget.plot_scatter(x,y,z,self.plot_id, self.plot_op_name)
        self.ui.plotWidget.canvas.figure.canvas.draw()
        self.ui.plotWidget.canvas.figure.canvas.flush_events()
        
        
        self.db.change_status = False

    def closeEvent(self, event):
        self.db.close()
        print("Closing ...")


    def abort_action(self):
        self.driver.abort()
        

    ###########
    # ACTIONS #
    ###########
    def move(self):
        x = [1, 2, 3*self.counter, 4, 5]
        y = [1, 2, 3, 4, 5]
        z = [1, 2, 3, 4, 5]
        self.ui.plotWidget.canvas.axes.clear()
        self.ui.plotWidget.plotScatter(x,y,z)
        self.ui.plotWidget.canvas.figure.canvas.draw()
        self.ui.plotWidget.canvas.figure.canvas.flush_events()
        self.counter = self.counter + 1

    def reference_z(self):
    # if self.state.value < State.CameraReady.value:
    #     print("Camera not ready")
    #     return
        self.ui.instructionLabel.setText("Select point for Z reference a hit reference Z")
        
        while len(imageHandler.points_struct) == 0:
            self.wait()
    
        pix_x,pix_y = imageHandler.points_struct[0][0],imageHandler.points_struct[0][1]
        imageHandler.updateImage.pause_updates = True
        try:
            self.driver.probe_in_camera_z_perspective(pix_x,pix_y)
            
            # x,y = self.driver.camera_to_cnc(pix_x,pix_y)
            # self.driver.move_to(x = x, y = y)
            # self.driver.probe_down()
        except AbortException:
            self.ui.instructionLabel.setText("Program was aborted")

        self.driver.cnc_s.poll()
        self.z_ref = self.driver.cnc_s.probed_position[2]
        self.clear_points()
        print("Probing done")
        print("Z height: {}".format(self.z_ref))
        return self.z_ref


    def find_position(self,func_text):
        imageHandler.updateImage.pause_updates = True
        if "inner" in func_text:
            z = self.reference_z()
        datalog = self.create_datalog(self.db, "Positions")
        self.ui.instructionLabel.setText("Select position")
        points = imageHandler.points_struct
        while True:
            if self.confirmed == True:
                if len(points) != 0:
                    break
                else:
                    self.ui.instructionLabel.setText("No points selected")
                    self.confirmed == False
            self.wait()
        
        for point in points:
            pix_x,pix_y = point[0],point[1]
            
            try:
                if "inner" in func_text:
                    self.driver.move_in_camera_z_perspective(pix_x, pix_y, z=self.z_ref)
                    self.driver.move_to(z=(self.z_ref-self.driver.probe_tip_diam),feedrate=1000)
                    if "hole" in func_text:
                        print("Holing")
                        self.driver.find_inner_circle_center(datalog=datalog)
                    elif "rectangle" in func_text:
                        print("Rectangling")
                        self.driver.find_inner_rectangle_center(datalog=datalog)
                if "outer" in func_text:
                    self.driver.probe_in_camera_z_perspective(pix_x, pix_y)
                    self.driver.cnc_s.poll()
                    self.z_ref = self.driver.cnc_s.probed_position[2]
                    self.driver.move_to(z=(self.z_ref+self.driver.probe_tip_diam),feedrate=1000)
                    if "hole" in func_text:
                        print("Holing")
                        self.driver.find_outer_circle_center(datalog=datalog)
                    elif "rectangle" in func_text:
                        print("Rectangling")
                        self.driver.find_outer_circle_center(datalog=datalog)
                else:
                    raise Exception("Unkown shape")
            except AbortException:
                self.ui.instructionLabel.setText("Program was aborted")
                return
            

    def scan_xy(self, func_text):
        self.state = State.Draw
        self.ui.instructionLabel.setText("Draw area to scan and hit confirm")
        
        while True:
            
            mask  = cv2.cvtColor(imageHandler.layers[imageHandler.layer],cv2.COLOR_BGR2GRAY)
            mask_exists =  np.count_nonzero(mask) != 0
            
            if self.confirmed == True:
                if mask_exists:
                    break
                else:
                    self.ui.instructionLabel.setText("No area selected")
                    self.confirmed == False
                
            self.wait()
        
        datalog = self.create_datalog(self.db, "XY scan")
        #datalog = None

        ind = np.argwhere(mask == np.amax(mask))
        y_ind = ind[:,0] 
        x_ind = ind[:,1]
        x_pix_min = np.min(x_ind, axis=None)
        x_pix_max = np.max(x_ind, axis=None)
        y_pix_min = np.min(y_ind, axis=None)
        y_pix_max = np.max(y_ind, axis=None)
        
        x_min, y_min = self.driver.camera_to_cnc(x_pix_max, y_pix_min) #Watch out, xmax <--> xmin is switched, image is reversed 
        x_max, y_max = self.driver.camera_to_cnc(x_pix_min, y_pix_max) #Watch out, xmax <--> xmin is switched, image is reversed 
        print(x_min, x_max, y_min, y_max)
        try:
            self.driver.scan_xy(x_min,x_max,y_min, y_max, datalog=datalog)
        except AbortException:
            self.ui.instructionLabel.setText("Program was aborted")

    def scan_line(self, func_text):
        self.state = State.SelectPoints 
        self.ui.instructionLabel.setText("Select end points")
        datalog = self.create_datalog(self.db, "Line scan")

        while len(imageHandler.points_struct) != 2:
            self.wait()
        pt0 = self.driver.camera_to_cnc(imageHandler.points_struct[0][0],imageHandler.points_struct[0][1])
        pt1 = self.driver.camera_to_cnc(imageHandler.points_struct[1][0],imageHandler.points_struct[1][1])
        try:    
            self.driver.scan_xy_line(pt0,pt1, datalog=datalog)
        except AbortException:
            self.ui.instructionLabel.setText("Program was aborted")

    def update_cnc(self):
        self.x_act, self.y_act, self.z_act = self.driver.get_actual_position()
        self.ui.xDro.setText("{:.3f}".format(self.x_act))
        self.ui.yDro.setText("{:.3f}".format(self.y_act))
        self.ui.zDro.setText("{:.3f}".format(self.z_act))

        self.driver.read_error_channel()

    def process_key(self,key):    
        if key == 27:
            return -1
        elif key == ord('0'):
            imageHandler.layer = 0
        elif key == ord('1'):
            imageHandler.layer = 1
        elif key == ord('2'):
            imageHandler.layer = 2
        elif key == ord('3'):
            imageHandler.layer = 3
        elif key == ord('4'):
            imageHandler.layer = 4      
        elif key == ord('R'):
            imageHandler.mode = 0
        elif key == ord('C'):
            imageHandler.mode = 1     
        elif key == ord('E'):
            imageHandler.mode = 2
        elif key == ord('L'):
            imageHandler.updateImage.pause_updates = not imageHandler.updateImage.pause_updates         
        elif key == ord('Q'):
            imageHandler.updateImage_to_default()
            self.state = State.CalibrateCamera
        elif key == ord('D'):
            imageHandler.delete_current_layer()  
        elif key == ord('H'):
            imageHandler.updateImage.printHelp = not imageHandler.updateImage.printHelp 
        elif key == ord('J'):
            self.state = State.Draw 
        return 0    
        

import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.th.win = w
    w.show()
    sys.exit(app.exec_())
    
