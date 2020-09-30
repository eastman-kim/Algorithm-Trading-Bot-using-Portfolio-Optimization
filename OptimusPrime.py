import sys
from PyQt5 import uic
from PyQt5 import QtGui
from kiwoom import *
from PortfolioOptimizer import *

form_class = uic.loadUiType("OptimusPrime.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.trade_stocks_done = False
        self.bucket = list()
        self.item_list = list()
        self.code_list = list()

        self.kiwoom = kiwoom()
        self.kiwoom.comm_connect()

        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)

        accounts_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")

        accounts_list = accounts.split(';')[0:accounts_num]
        self.comboBox.addItems(accounts_list)

        self.codeLineEdit.textChanged.connect(self.code_changed)
        self.viewButton.clicked.connect(self.check_balance)
        self.resetButton.clicked.connect(self.reset_bucket)
        self.addButton.clicked.connect(self.add_to_bucket)
        self.showButton.clicked.connect(self.show_bucket)
        self.downButton.clicked.connect(self.download_data)
        self.optButton.clicked.connect(self.optimize_weights)
        self.sendButton.clicked.connect(self.send_initial_order)
        self.spinBox.valueChanged.connect(self.asset_num)

        self.comboBox_2.addItems(accounts_list)

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox_2.currentText()
        order_type = self.comboBox_3.currentText()
        code = self.codeLineEdit_2.text()
        hoga = self.comboBox_4.currentText()
        num = self.spinBox_2.value()
        price = self.spinBox_3.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga], "")

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)
        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()

    # my portfolio
    def code_changed(self):
        code = self.codeLineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.nameLineEdit.setText(name)

    # manual order
    def code_changed_2(self):
        code = self.codeLineEdit_2.text()
        name = self.kiwoom.get_master_code_name(code)
        self.nameLineEdit_2.setText(name)

    def asset_num(self):
        self.num = self.spinBox.value()

    def reset_bucket(self):
        self.bucket = list()
        self.item_list = list()
        self.code_list = list()

    def add_to_bucket(self):
        code = self.codeLineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.nameLineEdit.setText(name)
        self.bucket.append([code, name])

    def show_bucket(self):
        item_count = len(self.bucket)
        print(self.num)
        if self.num != item_count:
            QMessageBox.about(self, "Warning!", "Item # is different from the number of assets added to your bucket!")
            return

        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]
        self.kiwoom.set_input_value("계좌번호", account_number)

        # Item list
        self.bucketTable.setRowCount(item_count)

        for j in range(item_count):
            row = self.bucket[j]
            self.code_list.append(row[0])
            self.item_list.append(row[1])
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                self.bucketTable.setItem(j, i, item)
        self.bucketTable.resizeRowsToContents()

    def download_data(self):
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]
        self.kiwoom.set_input_value("계좌번호", account_number)
        for code in self.code_list:
            self.kiwoom.get_ohlcv(code)
        QMessageBox.about(self, "Notification", "Download Completed")

    def optimize_weights(self):
        self.po = PortfolioOptimizer(self.code_list)
        QMessageBox.about(self, "Notification", "Calculation Completed")

    def send_initial_order(self):
        df = self.po.init_buy_list.reset_index()
        print("****** Proceeding my initial order ******")
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]
        self.kiwoom.set_input_value("계좌번호", account_number)
        for i in range(len(df)):
            print("{name}({code}) buy {quantity}".format(name=df.iloc[i][1], code=df.iloc[i][0], quantity=df.iloc[i][5]))
            self.kiwoom.send_order('order_req', '0101', account_number, 1, df.iloc[i][0], df.iloc[i][5], 0, '03', '')
        print("succeeded")
        QMessageBox.about(self, "Notification", "Order Completed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()