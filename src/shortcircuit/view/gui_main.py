# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_main.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(858, 905)
        font = QFont()
        font.setFamily(u"Segoe UI")
        font.setPointSize(9)
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(u":/images/app_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(330, 0))
        self.groupBox.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.lineEdit_source = QLineEdit(self.groupBox)
        self.lineEdit_source.setObjectName(u"lineEdit_source")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_source.sizePolicy().hasHeightForWidth())
        self.lineEdit_source.setSizePolicy(sizePolicy)
        self.lineEdit_source.setMaxLength(32)

        self.gridLayout.addWidget(self.lineEdit_source, 1, 1, 1, 1)

        self.label_destination = QLabel(self.groupBox)
        self.label_destination.setObjectName(u"label_destination")
        self.label_destination.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_destination, 3, 0, 1, 1)

        self.lineEdit_destination = QLineEdit(self.groupBox)
        self.lineEdit_destination.setObjectName(u"lineEdit_destination")
        self.lineEdit_destination.setMaxLength(32)

        self.gridLayout.addWidget(self.lineEdit_destination, 3, 1, 1, 1)

        self.label_source = QLabel(self.groupBox)
        self.label_source.setObjectName(u"label_source")
        self.label_source.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_source, 1, 0, 1, 1)

        self.pushButton_player_location = QPushButton(self.groupBox)
        self.pushButton_player_location.setObjectName(u"pushButton_player_location")
        self.pushButton_player_location.setEnabled(False)
        icon1 = QIcon()
        icon1.addFile(u":/images/crest_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_player_location.setIcon(icon1)

        self.gridLayout.addWidget(self.pushButton_player_location, 1, 2, 1, 1)

        self.pushButton_find_path = QPushButton(self.groupBox)
        self.pushButton_find_path.setObjectName(u"pushButton_find_path")

        self.gridLayout.addWidget(self.pushButton_find_path, 3, 2, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)

        self.label_status = QLabel(self.groupBox)
        self.label_status.setObjectName(u"label_status")

        self.gridLayout.addWidget(self.label_status, 4, 1, 1, 2)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.line = QFrame(self.groupBox)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.tableWidget_path = QTableWidget(self.groupBox)
        self.tableWidget_path.setObjectName(u"tableWidget_path")
        self.tableWidget_path.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_path.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_path.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_path.setRowCount(0)
        self.tableWidget_path.setColumnCount(0)

        self.verticalLayout_2.addWidget(self.tableWidget_path)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lineEdit_set_dest = QLineEdit(self.groupBox)
        self.lineEdit_set_dest.setObjectName(u"lineEdit_set_dest")
        self.lineEdit_set_dest.setMaximumSize(QSize(16777215, 16777215))
        self.lineEdit_set_dest.setMaxLength(32)

        self.gridLayout_3.addWidget(self.lineEdit_set_dest, 0, 1, 1, 1)

        self.pushButton_set_dest = QPushButton(self.groupBox)
        self.pushButton_set_dest.setObjectName(u"pushButton_set_dest")
        self.pushButton_set_dest.setEnabled(False)
        self.pushButton_set_dest.setIcon(icon1)

        self.gridLayout_3.addWidget(self.pushButton_set_dest, 0, 0, 1, 1)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)

        self.lineEdit_short_format = QLineEdit(self.groupBox)
        self.lineEdit_short_format.setObjectName(u"lineEdit_short_format")
        self.lineEdit_short_format.setReadOnly(True)

        self.gridLayout_3.addWidget(self.lineEdit_short_format, 1, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_3)


        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBox__options = QGroupBox(self.centralwidget)
        self.groupBox__options.setObjectName(u"groupBox__options")
        self.groupBox__options.setMinimumSize(QSize(290, 0))
        self.groupBox__options.setMaximumSize(QSize(290, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.groupBox__options)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.pushButton_trip_get = QPushButton(self.groupBox__options)
        self.pushButton_trip_get.setObjectName(u"pushButton_trip_get")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_trip_get.sizePolicy().hasHeightForWidth())
        self.pushButton_trip_get.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u":/images/tripwire_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_trip_get.setIcon(icon2)
        self.pushButton_trip_get.setIconSize(QSize(24, 24))

        self.gridLayout_4.addWidget(self.pushButton_trip_get, 1, 0, 1, 1)

        self.pushButton_eve_login = QPushButton(self.groupBox__options)
        self.pushButton_eve_login.setObjectName(u"pushButton_eve_login")
        self.pushButton_eve_login.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.pushButton_eve_login.sizePolicy().hasHeightForWidth())
        self.pushButton_eve_login.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u":/images/eve_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_eve_login.setIcon(icon3)
        self.pushButton_eve_login.setIconSize(QSize(24, 24))

        self.gridLayout_4.addWidget(self.pushButton_eve_login, 0, 0, 1, 1)

        self.pushButton_trip_config = QPushButton(self.groupBox__options)
        self.pushButton_trip_config.setObjectName(u"pushButton_trip_config")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_trip_config.sizePolicy().hasHeightForWidth())
        self.pushButton_trip_config.setSizePolicy(sizePolicy2)
        self.pushButton_trip_config.setMinimumSize(QSize(0, 0))
        self.pushButton_trip_config.setMaximumSize(QSize(16777215, 16777215))
        icon4 = QIcon()
        icon4.addFile(u":/images/config_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_trip_config.setIcon(icon4)

        self.gridLayout_4.addWidget(self.pushButton_trip_config, 1, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_4)

        self.groupBox_restrictions = QGroupBox(self.groupBox__options)
        self.groupBox_restrictions.setObjectName(u"groupBox_restrictions")
        self.groupBox_restrictions.setFlat(True)
        self.groupBox_restrictions.setAlignment(Qt.AlignHCenter)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_restrictions)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 5, 0, 5)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_5 = QLabel(self.groupBox_restrictions)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_4.addWidget(self.label_5)

        self.comboBox_size = QComboBox(self.groupBox_restrictions)
        self.comboBox_size.addItem("")
        self.comboBox_size.addItem("")
        self.comboBox_size.addItem("")
        self.comboBox_size.addItem("")
        self.comboBox_size.addItem("")
        self.comboBox_size.setObjectName(u"comboBox_size")
        self.comboBox_size.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)

        self.horizontalLayout_4.addWidget(self.comboBox_size)

        self.horizontalLayout_4.setStretch(0, 1)

        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.checkBox_eol = QCheckBox(self.groupBox_restrictions)
        self.checkBox_eol.setObjectName(u"checkBox_eol")

        self.verticalLayout_5.addWidget(self.checkBox_eol)

        self.checkBox_masscrit = QCheckBox(self.groupBox_restrictions)
        self.checkBox_masscrit.setObjectName(u"checkBox_masscrit")

        self.verticalLayout_5.addWidget(self.checkBox_masscrit)

        self.checkBox_ignore_old = QCheckBox(self.groupBox_restrictions)
        self.checkBox_ignore_old.setObjectName(u"checkBox_ignore_old")

        self.verticalLayout_5.addWidget(self.checkBox_ignore_old)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)

        self.doubleSpinBox_hours = QDoubleSpinBox(self.groupBox_restrictions)
        self.doubleSpinBox_hours.setObjectName(u"doubleSpinBox_hours")
        self.doubleSpinBox_hours.setDecimals(1)
        self.doubleSpinBox_hours.setMinimum(1.000000000000000)
        self.doubleSpinBox_hours.setMaximum(48.000000000000000)
        self.doubleSpinBox_hours.setSingleStep(0.500000000000000)
        self.doubleSpinBox_hours.setValue(16.000000000000000)

        self.horizontalLayout_6.addWidget(self.doubleSpinBox_hours)

        self.label_4 = QLabel(self.groupBox_restrictions)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_6.addWidget(self.label_4)


        self.verticalLayout_5.addLayout(self.horizontalLayout_6)


        self.verticalLayout_3.addWidget(self.groupBox_restrictions)

        self.groupBox_security = QGroupBox(self.groupBox__options)
        self.groupBox_security.setObjectName(u"groupBox_security")
        self.groupBox_security.setCheckable(True)
        self.groupBox_security.setFlat(True)
        self.groupBox_security.setAlignment(Qt.AlignHCenter)
        self.gridLayout_2 = QGridLayout(self.groupBox_security)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 5, 0, 5)
        self.spinBox_prio_hs = QSpinBox(self.groupBox_security)
        self.spinBox_prio_hs.setObjectName(u"spinBox_prio_hs")
        sizePolicy1.setHeightForWidth(self.spinBox_prio_hs.sizePolicy().hasHeightForWidth())
        self.spinBox_prio_hs.setSizePolicy(sizePolicy1)
        self.spinBox_prio_hs.setStyleSheet(u"QSpinBox { background-color: #DFF0D8; }")
        self.spinBox_prio_hs.setMinimum(1)
        self.spinBox_prio_hs.setMaximum(100)

        self.gridLayout_2.addWidget(self.spinBox_prio_hs, 1, 1, 1, 1)

        self.label_6 = QLabel(self.groupBox_security)
        self.label_6.setObjectName(u"label_6")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy3)

        self.gridLayout_2.addWidget(self.label_6, 2, 0, 1, 1)

        self.spinBox_prio_ns = QSpinBox(self.groupBox_security)
        self.spinBox_prio_ns.setObjectName(u"spinBox_prio_ns")
        sizePolicy1.setHeightForWidth(self.spinBox_prio_ns.sizePolicy().hasHeightForWidth())
        self.spinBox_prio_ns.setSizePolicy(sizePolicy1)
        self.spinBox_prio_ns.setStyleSheet(u"QSpinBox { background-color: #F2DEDE; }")
        self.spinBox_prio_ns.setMinimum(1)
        self.spinBox_prio_ns.setMaximum(100)

        self.gridLayout_2.addWidget(self.spinBox_prio_ns, 2, 1, 1, 1)

        self.label_10 = QLabel(self.groupBox_security)
        self.label_10.setObjectName(u"label_10")
        sizePolicy3.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy3)
        self.label_10.setOpenExternalLinks(True)

        self.gridLayout_2.addWidget(self.label_10, 2, 4, 1, 1)

        self.label_7 = QLabel(self.groupBox_security)
        self.label_7.setObjectName(u"label_7")
        sizePolicy3.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy3)

        self.gridLayout_2.addWidget(self.label_7, 1, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox_security)
        self.label_8.setObjectName(u"label_8")
        sizePolicy3.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy3)

        self.gridLayout_2.addWidget(self.label_8, 1, 2, 1, 1)

        self.spinBox_prio_wh = QSpinBox(self.groupBox_security)
        self.spinBox_prio_wh.setObjectName(u"spinBox_prio_wh")
        sizePolicy1.setHeightForWidth(self.spinBox_prio_wh.sizePolicy().hasHeightForWidth())
        self.spinBox_prio_wh.setSizePolicy(sizePolicy1)
        self.spinBox_prio_wh.setStyleSheet(u"QSpinBox { background-color: #D2E2F2; }")
        self.spinBox_prio_wh.setMinimum(1)
        self.spinBox_prio_wh.setMaximum(100)
        self.spinBox_prio_wh.setValue(1)

        self.gridLayout_2.addWidget(self.spinBox_prio_wh, 2, 3, 1, 1)

        self.label_9 = QLabel(self.groupBox_security)
        self.label_9.setObjectName(u"label_9")
        sizePolicy3.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy3)

        self.gridLayout_2.addWidget(self.label_9, 2, 2, 1, 1)

        self.spinBox_prio_ls = QSpinBox(self.groupBox_security)
        self.spinBox_prio_ls.setObjectName(u"spinBox_prio_ls")
        sizePolicy1.setHeightForWidth(self.spinBox_prio_ls.sizePolicy().hasHeightForWidth())
        self.spinBox_prio_ls.setSizePolicy(sizePolicy1)
        self.spinBox_prio_ls.setStyleSheet(u"QSpinBox { background-color: #FCF8E3; }")
        self.spinBox_prio_ls.setMinimum(1)
        self.spinBox_prio_ls.setMaximum(100)

        self.gridLayout_2.addWidget(self.spinBox_prio_ls, 1, 3, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_security)

        self.groupBox_avoidance = QGroupBox(self.groupBox__options)
        self.groupBox_avoidance.setObjectName(u"groupBox_avoidance")
        self.groupBox_avoidance.setCheckable(True)
        self.groupBox_avoidance.setFlat(True)
        self.groupBox_avoidance.setAlignment(Qt.AlignHCenter)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_avoidance)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 5, 0, 5)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_3 = QLabel(self.groupBox_avoidance)
        self.label_3.setObjectName(u"label_3")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy4)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.lineEdit_system_avoid_name = QLineEdit(self.groupBox_avoidance)
        self.lineEdit_system_avoid_name.setObjectName(u"lineEdit_system_avoid_name")
        sizePolicy5 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.lineEdit_system_avoid_name.sizePolicy().hasHeightForWidth())
        self.lineEdit_system_avoid_name.setSizePolicy(sizePolicy5)
        self.lineEdit_system_avoid_name.setMaxLength(32)

        self.horizontalLayout_2.addWidget(self.lineEdit_system_avoid_name)

        self.pushButton_system_avoid_add = QPushButton(self.groupBox_avoidance)
        self.pushButton_system_avoid_add.setObjectName(u"pushButton_system_avoid_add")
        sizePolicy2.setHeightForWidth(self.pushButton_system_avoid_add.sizePolicy().hasHeightForWidth())
        self.pushButton_system_avoid_add.setSizePolicy(sizePolicy2)
        self.pushButton_system_avoid_add.setMinimumSize(QSize(32, 0))
        self.pushButton_system_avoid_add.setMaximumSize(QSize(32, 16777215))
        self.pushButton_system_avoid_add.setLayoutDirection(Qt.LeftToRight)

        self.horizontalLayout_2.addWidget(self.pushButton_system_avoid_add)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_11 = QLabel(self.groupBox_avoidance)
        self.label_11.setObjectName(u"label_11")
        sizePolicy4.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy4)

        self.horizontalLayout_5.addWidget(self.label_11)

        self.lineEdit_region_avoid_name = QLineEdit(self.groupBox_avoidance)
        self.lineEdit_region_avoid_name.setObjectName(u"lineEdit_region_avoid_name")
        sizePolicy5.setHeightForWidth(self.lineEdit_region_avoid_name.sizePolicy().hasHeightForWidth())
        self.lineEdit_region_avoid_name.setSizePolicy(sizePolicy5)
        self.lineEdit_region_avoid_name.setMaxLength(32)

        self.horizontalLayout_5.addWidget(self.lineEdit_region_avoid_name)

        self.pushButton_region_avoid_add = QPushButton(self.groupBox_avoidance)
        self.pushButton_region_avoid_add.setObjectName(u"pushButton_region_avoid_add")
        sizePolicy2.setHeightForWidth(self.pushButton_region_avoid_add.sizePolicy().hasHeightForWidth())
        self.pushButton_region_avoid_add.setSizePolicy(sizePolicy2)
        self.pushButton_region_avoid_add.setMinimumSize(QSize(32, 0))
        self.pushButton_region_avoid_add.setMaximumSize(QSize(32, 16777215))
        self.pushButton_region_avoid_add.setLayoutDirection(Qt.LeftToRight)

        self.horizontalLayout_5.addWidget(self.pushButton_region_avoid_add)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.listWidget_avoid = QListWidget(self.groupBox_avoidance)
        self.listWidget_avoid.setObjectName(u"listWidget_avoid")
        self.listWidget_avoid.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout_4.addWidget(self.listWidget_avoid)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pushButton_avoid_delete = QPushButton(self.groupBox_avoidance)
        self.pushButton_avoid_delete.setObjectName(u"pushButton_avoid_delete")

        self.horizontalLayout_3.addWidget(self.pushButton_avoid_delete)

        self.pushButton_avoid_clear = QPushButton(self.groupBox_avoidance)
        self.pushButton_avoid_clear.setObjectName(u"pushButton_avoid_clear")
        icon5 = QIcon()
        icon5.addFile(u":/images/delete_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_avoid_clear.setIcon(icon5)

        self.horizontalLayout_3.addWidget(self.pushButton_avoid_clear)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)


        self.verticalLayout_3.addWidget(self.groupBox_avoidance)

        self.pushButton_reset = QPushButton(self.groupBox__options)
        self.pushButton_reset.setObjectName(u"pushButton_reset")

        self.verticalLayout_3.addWidget(self.pushButton_reset)


        self.horizontalLayout.addWidget(self.groupBox__options)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 858, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Route planner", None))
        self.label_destination.setText(QCoreApplication.translate("MainWindow", u"Destination:", None))
        self.lineEdit_destination.setPlaceholderText("")
        self.label_source.setText(QCoreApplication.translate("MainWindow", u"Source:", None))
        self.pushButton_player_location.setText(QCoreApplication.translate("MainWindow", u"Player location", None))
        self.pushButton_find_path.setText(QCoreApplication.translate("MainWindow", u"Find path", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Result:", None))
        self.label_status.setText(QCoreApplication.translate("MainWindow", u"Path status", None))
        self.pushButton_set_dest.setText(QCoreApplication.translate("MainWindow", u"Set in-game destination", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"FC, please help!", None))
        self.lineEdit_short_format.setPlaceholderText(QCoreApplication.translate("MainWindow", u"For quick copy-pasting of info", None))
        self.groupBox__options.setTitle(QCoreApplication.translate("MainWindow", u"Options", None))
        self.pushButton_trip_get.setText(QCoreApplication.translate("MainWindow", u"Get Tripwire Chain", None))
        self.pushButton_eve_login.setText(QCoreApplication.translate("MainWindow", u"Log in with EvE", None))
        self.pushButton_trip_config.setText(QCoreApplication.translate("MainWindow", u"Tripwire", None))
        self.groupBox_restrictions.setTitle(QCoreApplication.translate("MainWindow", u"Restrictions", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Wormhole size at least:", None))
        self.comboBox_size.setItemText(0, QCoreApplication.translate("MainWindow", u"Small [All]", None))
        self.comboBox_size.setItemText(1, QCoreApplication.translate("MainWindow", u"Medium", None))
        self.comboBox_size.setItemText(2, QCoreApplication.translate("MainWindow", u"Large", None))
        self.comboBox_size.setItemText(3, QCoreApplication.translate("MainWindow", u"X-Large", None))
        self.comboBox_size.setItemText(4, QCoreApplication.translate("MainWindow", u"[Ignore wormholes]", None))

        self.checkBox_eol.setText(QCoreApplication.translate("MainWindow", u"Ignore end of life wormholes", None))
        self.checkBox_masscrit.setText(QCoreApplication.translate("MainWindow", u"Ignore critical mass wormholes", None))
        self.checkBox_ignore_old.setText(QCoreApplication.translate("MainWindow", u"Ignore wormholes updated more than", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"hours ago", None))
        self.groupBox_security.setTitle(QCoreApplication.translate("MainWindow", u"Security prioritization", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"NS:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><a href=\"https://github.com/secondfry/shortcircuit/blob/master/README.md#security-prioritization\"><span style=\" text-decoration: underline; color:#0000ff;\">[?]</span></a></p></body></html>", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"HS:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"LS:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"WH:", None))
        self.groupBox_avoidance.setTitle(QCoreApplication.translate("MainWindow", u"Avoidance list", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"System:", None))
        self.pushButton_system_avoid_add.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Region:", None))
        self.pushButton_region_avoid_add.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.pushButton_avoid_delete.setText(QCoreApplication.translate("MainWindow", u"Delete selected", None))
        self.pushButton_avoid_clear.setText(QCoreApplication.translate("MainWindow", u"Clear list", None))
        self.pushButton_reset.setText(QCoreApplication.translate("MainWindow", u"Reset chain", None))
    # retranslateUi

