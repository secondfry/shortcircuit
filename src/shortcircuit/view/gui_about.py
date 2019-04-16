# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources\ui\gui_about.ui',
# licensing of 'resources\ui\gui_about.ui' applies.
#
# Created: Tue Apr 16 02:56:38 2019
#      by: pyside2-uic  running on PySide2 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(400, 260)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AboutDialog.sizePolicy().hasHeightForWidth())
        AboutDialog.setSizePolicy(sizePolicy)
        AboutDialog.setMinimumSize(QtCore.QSize(400, 260))
        AboutDialog.setMaximumSize(QtCore.QSize(400, 260))
        font = QtGui.QFont()
        font.setFamily("Arial")
        AboutDialog.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/app_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AboutDialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(AboutDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_title = QtWidgets.QLabel(AboutDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_title.sizePolicy().hasHeightForWidth())
        self.label_title.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label_title.setFont(font)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.label_title.setObjectName("label_title")
        self.horizontalLayout_3.addWidget(self.label_title)
        self.label_icon = QtWidgets.QLabel(AboutDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_icon.sizePolicy().hasHeightForWidth())
        self.label_icon.setSizePolicy(sizePolicy)
        self.label_icon.setText("")
        self.label_icon.setPixmap(QtGui.QPixmap(":/images/app_icon_small.png"))
        self.label_icon.setAlignment(QtCore.Qt.AlignCenter)
        self.label_icon.setObjectName("label_icon")
        self.horizontalLayout_3.addWidget(self.label_icon)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(AboutDialog)
        self.label_2.setStyleSheet("")
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_o7 = QtWidgets.QPushButton(AboutDialog)
        self.pushButton_o7.setObjectName("pushButton_o7")
        self.horizontalLayout.addWidget(self.pushButton_o7)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(AboutDialog)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(QtWidgets.QApplication.translate("AboutDialog", "About Short Circuit", None, -1))
        self.label_title.setText(QtWidgets.QApplication.translate("AboutDialog", "Short Circuit", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("AboutDialog", "<html>\n"
"<body>\n"
"<p>\n"
"    Short Circuit is an open-source application able to find the shortest path between solar systems (wormholes\n"
"    included) using the Eve SDE and wormhole mapping tools such as Tripwire. Short Circuit can run on all platforms\n"
"    where Python and PySide are supported.\n"
"</p>\n"
"<p>\n"
"    Original author – Valtyr Farshield.\n"
"</p>\n"
"<p><b>Maintainer list</b></p>\n"
"<ul>\n"
"    <li>@Second_Fry (Lenai Chelien).</li>\n"
"</ul>\n"
"<p><b>Credits</b></p>\n"
"<ul>\n"
"    <li>Daimian Mercer (Tripwire).</li>\n"
"    <li>Dreae (PyCrest).</li>\n"
"    <li>pyfa-org (PyFa).</li>\n"
"    <li>EvE-Scout.</li>\n"
"    <li>Sharps.</li>\n"
"    <li>choo t.</li>\n"
"</ul>\n"
"</body>\n"
"</html>\n"
"", None, -1))
        self.pushButton_o7.setText(QtWidgets.QApplication.translate("AboutDialog", "Fly safe o7", None, -1))

from . import resources_rc
