# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_wanderer.ui'
##
## Created by: Qt User Interface Compiler version 6.9.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QLineEdit, QSizePolicy,
    QWidget)
from . import resources_rc

class Ui_WandererDialog(object):
    def setupUi(self, WandererDialog):
        if not WandererDialog.objectName():
            WandererDialog.setObjectName(u"WandererDialog")
        WandererDialog.resize(480, 260)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WandererDialog.sizePolicy().hasHeightForWidth())
        WandererDialog.setSizePolicy(sizePolicy)
        WandererDialog.setMinimumSize(QSize(480, 260))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(9)
        WandererDialog.setFont(font)
        icon = QIcon()
        icon.addFile(u":/images/app_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        WandererDialog.setWindowIcon(icon)
        WandererDialog.setSizeGripEnabled(False)
        self.gridLayout = QGridLayout(WandererDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_name = QLabel(WandererDialog)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_name, 0, 0, 1, 1)

        self.lineEdit_name = QLineEdit(WandererDialog)
        self.lineEdit_name.setObjectName(u"lineEdit_name")

        self.gridLayout.addWidget(self.lineEdit_name, 0, 1, 1, 1)

        self.label_url = QLabel(WandererDialog)
        self.label_url.setObjectName(u"label_url")
        self.label_url.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_url, 1, 0, 1, 1)

        self.lineEdit_url = QLineEdit(WandererDialog)
        self.lineEdit_url.setObjectName(u"lineEdit_url")

        self.gridLayout.addWidget(self.lineEdit_url, 1, 1, 1, 1)

        self.label_map = QLabel(WandererDialog)
        self.label_map.setObjectName(u"label_map")
        self.label_map.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_map, 2, 0, 1, 1)

        self.lineEdit_map = QLineEdit(WandererDialog)
        self.lineEdit_map.setObjectName(u"lineEdit_map")

        self.gridLayout.addWidget(self.lineEdit_map, 2, 1, 1, 1)

        self.label_token = QLabel(WandererDialog)
        self.label_token.setObjectName(u"label_token")
        self.label_token.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_token, 3, 0, 1, 1)

        self.lineEdit_token = QLineEdit(WandererDialog)
        self.lineEdit_token.setObjectName(u"lineEdit_token")
        self.lineEdit_token.setInputMethodHints(Qt.ImhHiddenText|Qt.ImhNoAutoUppercase|Qt.ImhNoPredictiveText|Qt.ImhSensitiveData)
        self.lineEdit_token.setEchoMode(QLineEdit.Password)

        self.gridLayout.addWidget(self.lineEdit_token, 3, 1, 1, 1)

        self.label_help = QLabel(WandererDialog)
        self.label_help.setObjectName(u"label_help")
        self.label_help.setWordWrap(True)
        self.label_help.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.label_help.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.label_help, 4, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(WandererDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)


        self.retranslateUi(WandererDialog)
        self.buttonBox.accepted.connect(WandererDialog.accept)
        self.buttonBox.rejected.connect(WandererDialog.reject)

        QMetaObject.connectSlotsByName(WandererDialog)
    # setupUi

    def retranslateUi(self, WandererDialog):
        WandererDialog.setWindowTitle(QCoreApplication.translate("WandererDialog", u"Wanderer Configuration", None))
        self.label_name.setText(QCoreApplication.translate("WandererDialog", u"Name:", None))
        self.label_url.setText(QCoreApplication.translate("WandererDialog", u"URL:", None))
        self.lineEdit_url.setPlaceholderText(QCoreApplication.translate("WandererDialog", u"https://your-wanderer-instance", None))
        self.label_map.setText(QCoreApplication.translate("WandererDialog", u"Map slug:", None))
        self.lineEdit_map.setPlaceholderText(QCoreApplication.translate("WandererDialog", u"Map identifier from the map URL", None))
        self.label_token.setText(QCoreApplication.translate("WandererDialog", u"API token:", None))
        self.label_help.setText(QCoreApplication.translate("WandererDialog", u"<html><head/><body><p>Generate the token in Wanderer under Map Settings \u2192 API. <a href=\"https://github.com/wanderer-industries/wanderer\"><span style=\" text-decoration: underline; color:#0000ff;\">About Wanderer</span></a></p></body></html>", None))
    # retranslateUi

