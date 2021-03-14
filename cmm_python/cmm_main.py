import cv2
from cmm import Ui_MainWindow

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import imageHandler
import common

key = 255
class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        video_capture = imageHandler.camera_setup()                      
        while True:
            orig_img = cv2.cvtColor(imageHandler.next_frame2(video_capture), cv2.COLOR_BGR2RGB)

            if True:
                # https://stackoverflow.com/a/55468544/6622587
                #rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #cv2.namedWindow('test draw')
                #cv2.setMouseCallback('test draw',click_and_crop)
                global key
                
                if key is not 255:
                    imageHandler.process_key(key)
                    key = 255
                imageHandler.check_layers(orig_img)
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
        self.eventFlag = 0
    
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
        btn = self.ui.pushButton
        btn.clicked.connect(self.switch)
        th = Thread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        self.show()    

    def eventFilter(self, source, event):
        t = event.type()
        if t == QtCore.QEvent.MouseMove or t== QtCore.QEvent.MouseButtonPress or t== QtCore.QEvent.MouseButtonRelease :
            if imageHandler.eventFlag == 0:
                imageHandler.click_and_crop_qt(event,event.x(), event.y())
            else:
                imageHandler.object_drawing_qt(event,event.x(), event.y())
        return super(MainWindow, self).eventFilter(source, event)

    def keyPressEvent(self, event):
        global key 
        key = event.key()
        event.accept()

    def switch(self):
        self.ui.stackedWidget.setCurrentIndex(1) 

import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
