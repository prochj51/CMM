import cv2
from cmm import Ui_MainWindow

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from enum import Enum
import imageHandler
import linuxcnc_driver
import common

class State(Enum):
    CalibrateCamera = 1
    GetParams = 5
    SelectOrigin = 7
    CameraReady = 8
    Move = 9
    Reference_Z = 10
    Draw = 15

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

            if True:
                # https://stackoverflow.com/a/55468544/6622587
                #rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #cv2.namedWindow('test draw')
                #cv2.setMouseCallback('test draw',click_and_crop)
                if self.key is not 255:
                    imageHandler.process_key(self.key)
                    self.key = 255
                
                imageHandler.check_layers(orig_img)
                
                if self.win.state == State.CalibrateCamera:
                    self.win.ui.instructionLabel.setText("Select base plate points")
                    if imageHandler.warpImage():
                        self.win.state = State.GetParams
                        self.win.ui.instructionLabel.setText("Enter dimensions of base plate")
                
                elif self.win.state == State.SelectOrigin:
                    self.win.ui.instructionLabel.setText("Select [0,0] origin")
                    if imageHandler.addPoint(imageHandler.cnc_origin) == 1: 
                        self.win.state = State.Reference_Z
                
                # elif  self.win.state == State.CameraReady:
                #     self.win.state = State.Move #temporary       
                
                elif self.win.state == State.Reference_Z:
                    self.win.ui.instructionLabel.setText("Select point for Z reference a hit reference Z")
                    if imageHandler.addPoint(imageHandler.points2move) == 1: 
                        pass

                elif self.win.state == State.Move:
                    self.win.ui.instructionLabel.setText("Select point for probing")
                    if imageHandler.addPoint(imageHandler.points2move) == 1: 
                        pass 
                            
                
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
        self.initUI()
        self.state = State.CalibrateCamera
        self.driver = linuxcnc_driver.CncDriver()
        
    
    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))    
    def initUI(self):
        self.setWindowTitle("Win")
        #self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(1200, 800)
        # create a label
        self.label =self.ui.cvlabel
        self.label.move(280, 120)
        self.label.resize(640, 480)
        self.label.setMouseTracking(True)
        self.label.installEventFilter(self)
        self.ui.enterDimensionsButton.clicked.connect(self.processDimensions)
        self.ui.moveButton.clicked.connect(self.move)
        self.ui.referenceZ.clicked.connect(self.reference_z)
        self.ui.findeHoleCenter.clicked.connect(self.find_center)
        self.initStackLogic()
        self.selectedPoints = []
        self.th = Thread(self)
        self.th.changePixmap.connect(self.setImage)
        self.th.start()
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

    def initStackLogic(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.probeButton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentIndex(2))
        self.ui.scanButton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.goBackButton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.clickAndProbeButton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentIndex(3))
    
    def processDimensions(self):
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
    def move(self):
        if self.state < State.CameraReady:
            print("Camera not ready")
            return
        x,y = self.camera2cnc(imageHandler.points2move[0][0],imageHandler.points2move[0][1])
        imageHandler.updateImage.pause_updates = True
        self.driver.move_to(x=x,y=y,feedrate=1000)
    
    def reference_z(self):
        x,y = self.camera2cnc(imageHandler.points2move[0][0],imageHandler.points2move[0][1])
        imageHandler.updateImage.pause_updates = True
        self.driver.move_to(x=x,y=y,feedrate=1000)
        
        self.driver.ocode("o<down> call")
        self.driver.cnc_s.poll()
        self.reference_z = self.driver.cnc_s.probed_position[2]
        self.state = State.Move
    
    def find_center(self):
        x,y = self.camera2cnc(imageHandler.points2move[0][0],imageHandler.points2move[0][1])
        imageHandler.updateImage.pause_updates = True
        self.driver.move_to(x=x,y=y,feedrate=1000)
        self.driver.move_to(z=(self.reference_z-3),feedrate=1000)
        self.driver.find_hole_center()



    def camera2cnc(self,x,y):
        origin = imageHandler.cnc_origin[0]
        scale_x = self.calib_width/imageHandler.updateImage.calib_rect_width
        scale_y = self.calib_height/imageHandler.updateImage.calib_rect_height
        x0 = origin[0]
        y0 = origin[1]
        abs_x = scale_x*(x0 - x)
        abs_y = scale_y*(y - y0)
        return abs_x, abs_y

import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.th.win = w
    w.show()
    sys.exit(app.exec_())
