import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd


# class 이름 MyKiwoom2로 해야하나...
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        # self.OnReceiveChejanData.connect(self._receive_chejan_data)
    
    #main에서 로그인 할때 쓰는 method
    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")
    
        self.login_event_loop.exit()

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    
    # 메인 TR 처리 method (0계층/ event를 요청하고 기다림)
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("commRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])


    # 모의 투자는 주식 바로 입금 돼서 안쓰는 기능

    # fid = 체결잔고 아이템
    # def get_chejan_data(self, fid):
    #     ret = self.dynamicCall("GetChejanData(int)", fid)

    # def _receive_chejan_data(self, gubun, item_cnt, fid_list):
    #     print(gubun)

    #     print(self.get_chejan_data(9203))
    #     print(self.get_chejan_data(302))
    #     print(self.get_chejan_data(900))
    #     print(self.get_chejan_data(901))

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == "2":
            self.remained_data = True
        else:
            self.remained_data = False

        # TR link method
        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        elif rqname == "opt10001_req":
            self._opt10001(rqname, trcode)

        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    
    # opt 별 function(1계층/ event에 따라 어떻게 get_data 할지 정해짐)

    # opt10001
    def _opt10001(self, rqname, trcode):
        # 확인 요망: 4번째 arg 인 index 값은 무슨 의미? = 복수 데이터 인덱스래
        close = self._get_comm_data(trcode, rqname, 0, "현재가")    
        # 출력
        print(close)


    # opt10081
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        # #확인 요망... i 가 뭘 의미하지?? = 해당 item 번호/ nIndex – 복수데이터 인덱스
        for i in range(data_cnt):
            date = self._get_comm_data(trcode, rqname, i, "일자")
            open = self._get_comm_data(trcode, rqname, i, "시가")
            high = self._get_comm_data(trcode, rqname, i, "고가")
            low = self._get_comm_data(trcode, rqname, "저가")
            close = self._get_comm_data(trcode, rqname, i, "현재가")
            volume = self._get_comm_data(trcode, rqname, i, "거래량")

            self.ohlcv['close'].append(int(close))

            # 출력
            print("일봉 현재가 : ", close)

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret
    
    # opw00001
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._get_comm_data(trcode, rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    # opw00018
    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._get_comm_data(trcode, rqname, 0, "총매입금액")
        total_eval_price = self._get_comm_data(trcode, rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
        total_earning_rate = self._get_comm_data(trcode, rqname, 0, "총수익률(%)")
        estimated_deposit = self._get_comm_data(trcode, rqname, 0, "추정예탁자산")
        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        total_earning_rate = Kiwoom.change_format(total_earning_rate)
        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)
        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
            purchase_price = self._get_comm_data(trcode, rqname, i, "매입가")
            current_price = self._get_comm_data(trcode, rqname, i, "현재가")
            eval_profit_loss_price = self._get_comm_data(trcode, rqname, i, "평가손익")
            earning_rate = self._get_comm_data(trcode, rqname, i, "수익률(%)")
            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)
            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price, eval_profit_loss_price,
                                                  earning_rate])

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    # 변경된 API의 GET method (3계층/ Receive 된것에서 반복으로 가져옴)
    def _get_comm_data(self, code, field_name, index, item_name):
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)"
                                , code, field_name, index, item_name)
        return ret.strip()

    def _get_comm_rd(self, code, item_idx):
        ret = self.dynamicCall("GetCommRealData(QString, int)"
                                , code, item_idx)
        return ret.strip()
    


    # 기타 method 들
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name
    
    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun","")
        return ret


    @staticmethod
    def change_format(data):
        strip_data = data.lstrip("-0")
        if strip_data == "" or strip_data == ".00":
            strip_data = "0"

        try:
            format_data = format(int(strip_data), ",d")
        except:
            format_data = format(float(strip_data))
        if data.startswith("-"):
            format_data = "-" + format_data
        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'
        if strip_data.startswith('.'):
            strip_data = '0' + strip_data
        if data.startswith('-'):
            strip_data = '-' + strip_data
        return strip_data

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(";")[0]
    kiwoom.set_input_value("계좌번호", account_number)

    # Test
    i = 1
    print("--{}번째 값".format(i))

    # TR 별 set_input_value 수가 다르다
    kiwoom.set_input_value("종목코드", "039490")
    
    # 확인필요: 단순 조회에서도 next 값을 2로 넣어서 연속 조회를 나타내나? 1은 실시간 조회라는데
    kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")

    code_list = ["000020","000040","000050"]

    for c in code_list:
        i += 1
        print("--{}번째 값".format(i))
        time.sleep(0.5)
        kiwoom.set_input_value("종목코드", c)

        #next 값 2일때는 에러 나네...
        kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
        
    # test4 send order
    # (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
    kiwoom.send_order("order_req", "0101", account_number, "1", "005930", "10", 0, "03", "")
    time.sleep(5)   #체결까지 시간 좀 걸림

    # test2
    # set input value(여러번) 항상 확인해서 넣고 commreq해야함
    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.set_input_value("비밀번호","")
    kiwoom.set_input_value("비밀번호입력매체구분","")
    kiwoom.set_input_value("조회구분","2")

    kiwoom.reset_opw00018_output()
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "0101")
    print(kiwoom.opw00018_output['single'])
    print(kiwoom.opw00018_output['multi'])


    # test3 opt00018


