import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
#목표 
# print 마다 textedit.append() 함수 추가, print & append

#주의
# 모든 Rq는 Event Loop 필요 -> Slot 에서 .exit()
#  언제 발생할지 모르는 loop는 try except
# 변수들 type이 통일 안됨 00 != "00"
#  QString int 는 상관 없는 jeneric 임

# 확인 요망
#  주문 넣고 체결잔고 첫 메시지 안 기다려도 되나?(5초)
#  매수 매도 모두 "order_req" 로 label 해도 되나?


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

        # instance variable
        self.order_type_dict = {1:"신규매수", 2:"신규매도", 3:"매수취소", 4:"매도취소", 5:"매수정정", 6:"매도정정"}
        self.order_price_dict = {"00":"지정가", "03":"시장가", "05":"조건부지정가",
                "06":"최유리지정가", "07":"최우선지정가", "10":"지정가IOC", "13":"시장가IOC", 
                "16":"최유리IOC", "20":"지정가FOK", "23":"시장가FOK", "26":"최유리FOK",
                 "61":"장전시간외종가", "62":"시간외단일가", "81":"장후시간외종가"}
        self.code_dict = {"동화약품":"000020","KR모터스":"000040","경방":"000050", "메리츠화재":"000060", 
                "삼양홀딩스":"000070", "하이트진로":"000080","유한양행":"000100","CJ대한통운":"000120","두산":"000150","삼성전자":"005930"}
        self.code_list = ["000020","000040","000050","000060","000070","000080","000100","000120","000150","005930"]
        self.gubun_dict = {0:"주문체결통보", 1:"잔고통보", 3:"특이신호"}
        self.msg_cnt = [0,0,0]

        # output["multi"]를 만들어 놓기 위해 진행 되는 선택적 부분
        self.comm_connect()
        self.account_number = self.get_login_info("ACCNO")
        self.account_number = self.account_number.split(";")[0]

        # 조회를 통해 output["multi"] 생성(input 값 뒷부분은 안보내도 괜찮음(비번구분 등))
        self.set_input_value("계좌번호", self.account_number)

        self.reset_opw00018_output()
        self.comm_rq_data("opw00018_req", "opw00018", 0, "0101")
        print(self.opw00018_output["multi"])


    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        print("System>>> kiwoom instance created")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        print("System>>> slots connected with events")


    # [0계층] 
        #(TR 처리 method)(loop must start)(self, KOA tr required arg)
        # TR별 KOA 입력값 참고
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString,QString)", id, value)
        # no loop needed

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("commRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        self.chejan_loop = QEventLoop()
        print("System>>> '{} {}주 {}로 {} 주문중...'".format(
                list(self.code_dict.keys())[list(self.code_dict.values()).index(code)],
                quantity, self.order_price_dict[price], self.order_type_dict[int(order_type)]))        
        print("System>>> Order sent and waitting for first call back...")
        self.chejan_loop.exec_()


    # [1계층] 
        # (Event 처리 Slot methods) (self, OnRecieve 반환값)
        # 0계층 -> Event -> 1계층(slot)(loop must end)
        # 로그인 Event
    def _event_connect(self, err_code):
        if err_code == 0:
            print("System>>> logged in")
        else:
            print("System>>> failed to login")
        
        self.login_event_loop.exit()

        # TR Event 처리
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # 한 TR에 20개밖에 못들고옴, 넘어갈 경우 연속 조회가 됨(opt100001)
        if next == "2":
            self.remained_data = True
        else:
            self.remained_data = False

        # TR link method
        if rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()   # 해당 loop가 없는채로 Event가 일어나면
        except AttributeError:
            pass
    
    # [2계층]
        # opw00001 예수금 상세 현황(2일 후 들어오니까 이게 더 맞는 port value 일지도)
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._get_comm_data(trcode, rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

        # opw00018 계좌 평가 잔고 내역 요청
    def _opw00018(self, rqname, trcode):

        # single data
        print("System>>> constructing opw00018 output[single]...")
        total_purchase_price = self._get_comm_data(trcode, rqname, 0, "총매입금액")
        total_eval_price = self._get_comm_data(trcode, rqname, 0, "총평가금액")
        # total_eval_profit_loss_price = self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
        # total_earning_rate = self._get_comm_data(trcode, rqname, 0, "총수익률(%)")
        estimated_deposit = self._get_comm_data(trcode, rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))
        print("System>>> opw00018 output[single] constructed")

        # # 모의투자는 수익률 표시 형식이 다름
        # total_earning_rate = Kiwoom.change_format(total_earning_rate)
        # if self.get_server_gubun():
        #     total_earning_rate = float(total_earning_rate) / 100
        #     total_earning_rate = str(total_earning_rate)
        # self.opw00018_output['single'].append(total_earning_rate)
        
        # multi data
            # item 별로 구분 줄 필요가 있는 경우 multidata로 들여옴
            # 이 경우 종목 코드별 item page 구분
                    # data_cnt = nIndex – 복수데이터 인덱스
                    # return 되는 정보 더 많음, 필요한것만 받은 상황
        print("System>>> constructing opw00018 output[multi]...")
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
            current_price = self._get_comm_data(trcode, rqname, i, "현재가")

            quantity = Kiwoom.change_format(quantity)
            current_price = Kiwoom.change_format(current_price)

            self.opw00018_output['multi'].append([name, quantity, current_price])
        print("System>>> opw00018 output[multi] constructed")

        # 체결잔고 통지 Event 처리
        # fid == 구분, 주문번호, 종목명, 주문수량, 주문가격
        # gubun == 0:주문체결통보, 1:잔고통보, 3:특이신호
            # 시장가에 매물 없을시 주문체결통보가 여러번 올 수 있음
            # 주문체결통보 한번만 확인하고 다음 주문 넘어가면 됨
            # 잔고통보 가끔 오는데 무시해도 괜찮음
    def _receive_chejan_data(self, fid):
        self.chejan_gubun = int(gubun)

        self.msg_cnt[self.chejan_gubun] += 1

        print("System>>> total of {} message about {} recieved"
        .format(self.msg_cnt[self.chejan_gubun], self.gubun_dict[self.chejan_gubun]))

        # 첫 주문체결통보에서 event exit
            # 다른 종목의 추가 체결통보와 겹칠 수 있음으로 예외처리 필요
            # 모의투자는 종목명이 안뜸으로 sleep 으로 기다려야함
            # 모든 주문 체결까지 기다리는 알고리즘은 예전 파일에 존재 keep_buying_loop

        if self.chejan_gubun == 0:
            # 모의투자여서 무작정 기다려야함(모든 거래 다 체결 되는거 기다리는 방법도 있음)
            print("System>>> New Order made, must wait 5 seconds")
            time.sleep(5)
            self.chejan_loop.exit()
    

    # main에서 쓸(== 0계층) TR이 아닌 method
        # 로그인
    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        print("System>>> logging in...")
        self.login_event_loop.exec_()

        # opw output 여기서 처음 만들어짐
    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

        # export 해야할 정보
    def get_current_info(self):
        self.set_input_value("계좌번호", self.account_number)
        self.reset_opw00018_output()
        self.comm_rq_data("opw00018_req", "opw00018", 0, "0101")
        ret = pd.DataFrame(self.opw00018_output["multi"],
                        columns=["종목명","보유수량","현재가"])
        return ret

    def bid_mrk_order(self, stock_code, quantity):
        self.send_order("order_req", "0101", self.account_number, "1", stock_code, quantity, "03", 0, "")

    def ask_mrk_order(self, stock_code, quantity):
        self.send_order("order_req", "0101", self.account_number, "2", stock_code, quantity, "03", 0, "")
        
    
    # [3계층 method]
        # 변경된 API의 GET method (Receive 된것에서 반복으로 가져옴)
        # opt 여러가지 쓰다보면 req_name 이 서로 달라야 찾을 수 있다.
    def _get_comm_data(self, code, req_name, index, item_name):
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)"
                                , code, req_name, index, item_name)
        return ret.strip()

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret
    
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
    print(kiwoom.get_current_info())

    kiwoom.bid_mrk_order(kiwoom.code_list[0],10)
    print("function working")