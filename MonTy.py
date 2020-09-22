import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from PortfolioOptimizer import *


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonT")
        self.setGeometry(300, 300, 300, 150)

        # Kiwoom Login
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.dynamicCall("CommConnect(")

        # OpenAPI Events
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)

        # Window Settings
        self.setWindowTitle("MonTy")
        self.setGeometry(300,300,300,150)

        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10,60,280,80)
        self.text_edit.setEnabled(False) # Read mode only

        btn1 = QPushButton("Weight Opt",self)
        btn1.move(40, 20)
        btn1.clicked.connect(self.btn1_clicked)

        btn2 = QPushButton("Rebalance", self)
        btn2.move(160, 20)
        btn1.clicked.connect(self.btn1_clicked)

    def btn1_clicked(self):
        self.text_edit.append("Optimizing Weights...")
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        if PortfolioOptimizer.opt_weight(): self.text_edit.append("Successful")
        else: self.text_edit.append("Failed")

    def btn2_clicked(self):
        self.text_edit.append("Rebalancing...")
        if PortfolioOptimizer.rebalance(): self.text_edit.append("Successful")
        else: self.text_edit.append("Failed")

    # Event handler
    def event_connect(self,err_code):
        if err_code == 0: self.text_edit.append("Welcome, I am MonTy.")
        else: self.text_edit.append("로그인 실패")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()