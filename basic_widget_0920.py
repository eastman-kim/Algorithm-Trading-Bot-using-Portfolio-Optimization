import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from MyKiwoom import *

class MyWindow(QMainWindow):
    def __init__(self):

        #super 인 QMainWindow의 instance variable 다 가져옴
        super().__init__()

        #window 설정
        self.setWindowTitle("PyStock")
        self.setGeometry(300,300,300,150)

        #MyKiwoom.py debugging 용
        btn3 = QPushButton("Debug", self)
        btn3.move(90, 50)
        btn3.clicked.connect(self.btn3_clicked)

        #Update weight 버튼
        btn1 = QPushButton("Update_Weight", self)
        btn1.move(30, 20)
        btn1.clicked.connect(self.btn1_clicked)

        #Update rebalance 버튼
        btn2 = QPushButton("Rebalance", self)
        btn2.move(150, 20)
        btn2.clicked.connect(self.btn2_clicked)

        #표시 정보창
        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10, 80, 280, 80)
        self.text_edit.setEnabled(False)

        #Weidget 과 Kiwoom 연결
        self.MyKiwoom = MyKiwoom(self)


        


    
    def btn1_clicked(self):
        self.text_edit.clear()      
        # self.text_edit.append(time.clock_gettime)
        # weight calc function import
        pass
    
    def btn2_clicked(self):
        self.text_edit.clear()
        # self.text_edit.append(time.clock_gettime)
        # rebalancing function import
        pass


    def btn3_clicked(self):
        self.text_edit.clear()
        self.text_edit.append("MyKiwoom.py Debugging")
        # MyKiwoom.py debugging 용 update랑 관계 없음
        self.MyKiwoom.price_enumer()
        print(self.MyKiwoom.temp_price)
        
        pass

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
