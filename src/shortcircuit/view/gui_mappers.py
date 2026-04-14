# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_mappers.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_MappersDialog(object):
    def setupUi(self, MappersDialog):
        if not MappersDialog.objectName():
            MappersDialog.setObjectName(u"MappersDialog")
        MappersDialog.resize(560, 360)
        MappersDialog.setMinimumSize(QSize(560, 360))
        font = QFont()
        font.setFamily(u"Segoe UI")
        font.setPointSize(9)
        MappersDialog.setFont(font)
        icon = QIcon()
        icon.addFile(u":/images/app_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        MappersDialog.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(MappersDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_intro = QLabel(MappersDialog)
        self.label_intro.setObjectName(u"label_intro")
        self.label_intro.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_intro)

        self.tableWidget_mappers = QTableWidget(MappersDialog)
        self.tableWidget_mappers.setObjectName(u"tableWidget_mappers")
        self.tableWidget_mappers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_mappers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget_mappers.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_mappers.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout.addWidget(self.tableWidget_mappers)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pushButton_add = QPushButton(MappersDialog)
        self.pushButton_add.setObjectName(u"pushButton_add")

        self.horizontalLayout_buttons.addWidget(self.pushButton_add)

        self.pushButton_edit = QPushButton(MappersDialog)
        self.pushButton_edit.setObjectName(u"pushButton_edit")

        self.horizontalLayout_buttons.addWidget(self.pushButton_edit)

        self.pushButton_remove = QPushButton(MappersDialog)
        self.pushButton_remove.setObjectName(u"pushButton_remove")

        self.horizontalLayout_buttons.addWidget(self.pushButton_remove)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)

        self.buttonBox = QDialogButtonBox(MappersDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(MappersDialog)
        self.buttonBox.accepted.connect(MappersDialog.accept)
        self.buttonBox.rejected.connect(MappersDialog.reject)

        QMetaObject.connectSlotsByName(MappersDialog)
    # setupUi

    def retranslateUi(self, MappersDialog):
        MappersDialog.setWindowTitle(QCoreApplication.translate("MappersDialog", u"Mappers", None))
        self.label_intro.setText(QCoreApplication.translate("MappersDialog", u"Configure one or more wormhole mapper sources. All enabled mappers are queried together when you click \"Get Data\".", None))
        self.pushButton_add.setText(QCoreApplication.translate("MappersDialog", u"Add\u2026", None))
        self.pushButton_edit.setText(QCoreApplication.translate("MappersDialog", u"Edit\u2026", None))
        self.pushButton_remove.setText(QCoreApplication.translate("MappersDialog", u"Remove", None))
    # retranslateUi

