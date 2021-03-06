# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cmm.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 1078)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridFrame = QtWidgets.QFrame(self.centralwidget)
        self.gridFrame.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gridFrame.sizePolicy().hasHeightForWidth())
        self.gridFrame.setSizePolicy(sizePolicy)
        self.gridFrame.setStyleSheet("QPushButton{\n"
"background-color: red;\n"
"max-height:40px;\n"
"}")
        self.gridFrame.setObjectName("gridFrame")
        self.gridLayout = QtWidgets.QGridLayout(self.gridFrame)
        self.gridLayout.setObjectName("gridLayout")
        self.leftVerticalFrame = QtWidgets.QFrame(self.gridFrame)
        self.leftVerticalFrame.setObjectName("leftVerticalFrame")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.leftVerticalFrame)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.comboBox = QtWidgets.QComboBox(self.leftVerticalFrame)
        self.comboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout_9.addWidget(self.comboBox)
        self.startButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.startButton.setObjectName("startButton")
        self.verticalLayout_9.addWidget(self.startButton)
        self.confirmButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.confirmButton.setObjectName("confirmButton")
        self.verticalLayout_9.addWidget(self.confirmButton)
        self.abortButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.abortButton.setObjectName("abortButton")
        self.verticalLayout_9.addWidget(self.abortButton)
        self.clearPointsButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.clearPointsButton.setObjectName("clearPointsButton")
        self.verticalLayout_9.addWidget(self.clearPointsButton)
        self.horizontalFrame = QtWidgets.QFrame(self.leftVerticalFrame)
        self.horizontalFrame.setObjectName("horizontalFrame")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.horizontalFrame)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.label_4 = QtWidgets.QLabel(self.horizontalFrame)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_5.addWidget(self.label_4)
        self.label_3 = QtWidgets.QLabel(self.horizontalFrame)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_5.addWidget(self.label_3)
        self.verticalLayout_9.addWidget(self.horizontalFrame)
        self.droFrame = QtWidgets.QFrame(self.leftVerticalFrame)
        self.droFrame.setObjectName("droFrame")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.droFrame)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.xDro = QtWidgets.QLabel(self.droFrame)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.xDro.setFont(font)
        self.xDro.setObjectName("xDro")
        self.horizontalLayout_4.addWidget(self.xDro)
        self.yDro = QtWidgets.QLabel(self.droFrame)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.yDro.setFont(font)
        self.yDro.setObjectName("yDro")
        self.horizontalLayout_4.addWidget(self.yDro)
        self.zDro = QtWidgets.QLabel(self.droFrame)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.zDro.setFont(font)
        self.zDro.setObjectName("zDro")
        self.horizontalLayout_4.addWidget(self.zDro)
        self.verticalLayout_9.addWidget(self.droFrame)
        self.instructionLabel = QtWidgets.QLabel(self.leftVerticalFrame)
        font = QtGui.QFont()
        font.setFamily("Quicksand Medium")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.instructionLabel.setFont(font)
        self.instructionLabel.setObjectName("instructionLabel")
        self.verticalLayout_9.addWidget(self.instructionLabel)
        self.horizontalFrame1 = QtWidgets.QFrame(self.leftVerticalFrame)
        self.horizontalFrame1.setObjectName("horizontalFrame1")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalFrame1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.horizontalFrame1)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.widthInput = QtWidgets.QLineEdit(self.horizontalFrame1)
        self.widthInput.setObjectName("widthInput")
        self.horizontalLayout_2.addWidget(self.widthInput)
        self.verticalLayout_9.addWidget(self.horizontalFrame1)
        self.horizontalFrame2 = QtWidgets.QFrame(self.leftVerticalFrame)
        self.horizontalFrame2.setObjectName("horizontalFrame2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalFrame2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(self.horizontalFrame2)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.heightInput = QtWidgets.QLineEdit(self.horizontalFrame2)
        self.heightInput.setObjectName("heightInput")
        self.horizontalLayout_3.addWidget(self.heightInput)
        self.verticalLayout_9.addWidget(self.horizontalFrame2)
        self.enterDimensionsButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.enterDimensionsButton.setObjectName("enterDimensionsButton")
        self.verticalLayout_9.addWidget(self.enterDimensionsButton)
        self.homeAllButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.homeAllButton.setObjectName("homeAllButton")
        self.verticalLayout_9.addWidget(self.homeAllButton)
        self.goToHomeButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.goToHomeButton.setObjectName("goToHomeButton")
        self.verticalLayout_9.addWidget(self.goToHomeButton)
        self.moveButton = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.moveButton.setObjectName("moveButton")
        self.verticalLayout_9.addWidget(self.moveButton)
        self.referenceZ = QtWidgets.QPushButton(self.leftVerticalFrame)
        self.referenceZ.setObjectName("referenceZ")
        self.verticalLayout_9.addWidget(self.referenceZ)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_9.addItem(spacerItem)
        self.gridLayout.addWidget(self.leftVerticalFrame, 0, 0, 1, 1)
        self.rightVerticalFrame = QtWidgets.QFrame(self.gridFrame)
        self.rightVerticalFrame.setObjectName("rightVerticalFrame")
        self.right = QtWidgets.QVBoxLayout(self.rightVerticalFrame)
        self.right.setObjectName("right")
        self.plotWidget = MplWidget(self.rightVerticalFrame)
        self.plotWidget.setMinimumSize(QtCore.QSize(0, 350))
        self.plotWidget.setObjectName("plotWidget")
        self.right.addWidget(self.plotWidget)
        self.cvlabel = QtWidgets.QLabel(self.rightVerticalFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cvlabel.sizePolicy().hasHeightForWidth())
        self.cvlabel.setSizePolicy(sizePolicy)
        self.cvlabel.setMinimumSize(QtCore.QSize(640, 480))
        self.cvlabel.setMaximumSize(QtCore.QSize(640, 480))
        self.cvlabel.setObjectName("cvlabel")
        self.right.addWidget(self.cvlabel)
        self.gridLayout.addWidget(self.rightVerticalFrame, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.gridFrame, 0, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.startButton.setText(_translate("MainWindow", "Start"))
        self.confirmButton.setText(_translate("MainWindow", "Confirm"))
        self.abortButton.setText(_translate("MainWindow", "Abort"))
        self.clearPointsButton.setText(_translate("MainWindow", "Clear selected points"))
        self.label_5.setText(_translate("MainWindow", "X"))
        self.label_4.setText(_translate("MainWindow", "Y"))
        self.label_3.setText(_translate("MainWindow", "Z"))
        self.xDro.setText(_translate("MainWindow", "0.000"))
        self.yDro.setText(_translate("MainWindow", "0.000"))
        self.zDro.setText(_translate("MainWindow", "0.000"))
        self.instructionLabel.setText(_translate("MainWindow", "Follow instruction"))
        self.label.setText(_translate("MainWindow", "Width"))
        self.widthInput.setText(_translate("MainWindow", "235"))
        self.label_2.setText(_translate("MainWindow", "Height"))
        self.heightInput.setText(_translate("MainWindow", "235"))
        self.enterDimensionsButton.setText(_translate("MainWindow", "Enter dimensions"))
        self.homeAllButton.setText(_translate("MainWindow", "Home All"))
        self.goToHomeButton.setText(_translate("MainWindow", "Go to Home"))
        self.moveButton.setText(_translate("MainWindow", "Move"))
        self.referenceZ.setText(_translate("MainWindow", "Reference Z"))
        self.cvlabel.setText(_translate("MainWindow", "Camera"))

from mplwidget import MplWidget
