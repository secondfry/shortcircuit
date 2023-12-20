# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_tripwire.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_TripwireDialog(object):
    def setupUi(self, TripwireDialog):
        if not TripwireDialog.objectName():
            TripwireDialog.setObjectName(u"TripwireDialog")
        TripwireDialog.resize(400, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(TripwireDialog.sizePolicy().hasHeightForWidth())
        TripwireDialog.setSizePolicy(sizePolicy)
        TripwireDialog.setMinimumSize(QSize(400, 300))
        TripwireDialog.setMaximumSize(QSize(400, 300))
        font = QFont()
        font.setFamily(u"Segoe UI")
        font.setPointSize(9)
        TripwireDialog.setFont(font)
        icon = QIcon()
        icon.addFile(u":/images/app_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        TripwireDialog.setWindowIcon(icon)
        TripwireDialog.setSizeGripEnabled(False)
        self.gridLayout = QGridLayout(TripwireDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_2 = QLabel(TripwireDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.label = QLabel(TripwireDialog)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.checkBox_evescout = QCheckBox(TripwireDialog)
        self.checkBox_evescout.setObjectName(u"checkBox_evescout")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.checkBox_evescout.sizePolicy().hasHeightForWidth())
        self.checkBox_evescout.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.checkBox_evescout)

        self.label_6 = QLabel(TripwireDialog)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setOpenExternalLinks(True)

        self.horizontalLayout.addWidget(self.label_6)


        self.gridLayout.addLayout(self.horizontalLayout, 6, 1, 1, 1)

        self.label_3 = QLabel(TripwireDialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(TripwireDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 11, 0, 1, 2)

        self.label_evescout_logo = QLabel(TripwireDialog)
        self.label_evescout_logo.setObjectName(u"label_evescout_logo")
        self.label_evescout_logo.setCursor(QCursor(Qt.PointingHandCursor))
        self.label_evescout_logo.setPixmap(QPixmap(u":/images/evescout.png"))
        self.label_evescout_logo.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_evescout_logo, 5, 0, 4, 1)

        self.lineEdit_url = QLineEdit(TripwireDialog)
        self.lineEdit_url.setObjectName(u"lineEdit_url")

        self.gridLayout.addWidget(self.lineEdit_url, 1, 1, 1, 1)

        self.lineEdit_user = QLineEdit(TripwireDialog)
        self.lineEdit_user.setObjectName(u"lineEdit_user")

        self.gridLayout.addWidget(self.lineEdit_user, 2, 1, 1, 1)

        self.lineEdit_pass = QLineEdit(TripwireDialog)
        self.lineEdit_pass.setObjectName(u"lineEdit_pass")
        self.lineEdit_pass.setInputMethodHints(Qt.ImhHiddenText|Qt.ImhNoAutoUppercase|Qt.ImhNoPredictiveText|Qt.ImhSensitiveData)
        self.lineEdit_pass.setEchoMode(QLineEdit.Password)

        self.gridLayout.addWidget(self.lineEdit_pass, 3, 1, 1, 1)

        self.label_5 = QLabel(TripwireDialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.label_5.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.label_5, 7, 1, 1, 1)

        self.label_4 = QLabel(TripwireDialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setPixmap(QPixmap(u":/images/tripwire_banner.png"))

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 2)

        self.label_7 = QLabel(TripwireDialog)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_7, 4, 0, 1, 1)

        self.lineEdit_proxy = QLineEdit(TripwireDialog)
        self.lineEdit_proxy.setObjectName(u"lineEdit_proxy")

        self.gridLayout.addWidget(self.lineEdit_proxy, 4, 1, 1, 1)


        self.retranslateUi(TripwireDialog)
        self.buttonBox.accepted.connect(TripwireDialog.accept)
        self.buttonBox.rejected.connect(TripwireDialog.reject)

        QMetaObject.connectSlotsByName(TripwireDialog)
    # setupUi

    def retranslateUi(self, TripwireDialog):
        TripwireDialog.setWindowTitle(QCoreApplication.translate("TripwireDialog", u"Tripwire Configuration", None))
        self.label_2.setText(QCoreApplication.translate("TripwireDialog", u"Username:", None))
        self.label.setText(QCoreApplication.translate("TripwireDialog", u"URL:", None))
#if QT_CONFIG(tooltip)
        self.checkBox_evescout.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.checkBox_evescout.setText(QCoreApplication.translate("TripwireDialog", u"Enable Eve-Scout", None))
        self.label_6.setText(QCoreApplication.translate("TripwireDialog", u"<html><head/><body><p><a href=\"https://github.com/secondfry/shortcircuit/blob/master/README.md#eve-scout\"><span style=\" text-decoration: underline; color:#0000ff;\">[Should I enable this?]</span></a></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("TripwireDialog", u"Password:", None))
        self.label_evescout_logo.setText("")
        self.label_5.setText(QCoreApplication.translate("TripwireDialog", u"<html><head/><body><p><a href=\"https://tripwire.eve-apps.com/\"><span style=\" text-decoration: underline; color:#0000ff;\">Don't have a Tripwire account, yet?</span></a></p></body></html>", None))
        self.label_4.setText("")
        self.label_7.setText(QCoreApplication.translate("TripwireDialog", u"Proxy:", None))
        self.lineEdit_proxy.setInputMask("")
        self.lineEdit_proxy.setPlaceholderText(QCoreApplication.translate("TripwireDialog", u"Leave empty to disable", None))
    # retranslateUi

