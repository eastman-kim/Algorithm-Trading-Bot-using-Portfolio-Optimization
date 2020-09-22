import sys
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
import time


class kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        """
        이벤트 처리 함수
        """
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)

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

    def get_code_list_by_market(self, market):
        # 장구분별 종목코드 리스트를 반환
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        # 종목코드의 종목이름 반환
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        # 통신 접속 상태 반환
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def get_login_info(self, tag):
        # 로그인 정보 반환
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def set_input_value(self, id, value):
        # 입력 데이터 설정
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        """
         Transaction 서버로 송신
        :param rqname: 사용자구분 이름
        :param trcode: Transaction 이름 입력
        :param next:  0: 조회, 2: 연속
        :param screen_no: 화면번호 (0101)
        :return: 에러 반환
        """
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _get_comm_data(self, tr_code, record_name, index, item_name):
        """
        조회 데이터 반환
        :param tr_code: 거래 코드
        :param record_name: 레코드명
        :param index: 복수데이터 인덱스
        :param item_name: 아이템명
        :return: 수신 데이터
        ex) 현재가 출력 - openApi.GetCommData("opt00001","주식기본정보",0,"현재가")
        """
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               tr_code, record_name, index, item_name)
        return ret.strip()

    def _get_comm_real_data(self, code, fid):
        """
        :param code: 종목코드
        :param fid: 실시간 아이템
        :return: 수신 데이터
        ex) 현재가 출력 - openApi.GetCommRealData("039490",10) code는 onReceiveRealData 첫번째 매개변수 사용
        """
        ret = self.dynamicCall("GetCommData(QString, int)",  code, fid)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        """
        레코드 반복횟수를 반환
        :param trcode: Tran명
        :param rqname: 레코드명
        :return: 레코드 반복횟수
        """
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        """
        주식 주문을 서버로 전송
        :param rqname: 사용자 구분 요청 이름
        :param screen_no: 화면번호 4자리
        :param acc_no: 계좌번호 10자리
        :param order_type: 주문유형 (1.신규매수 2.신규매도 3.매수취소 4.매도취소 5.매수정정 6.매도정정)
        :param code: 종목코드
        :param quantity: 주문수량
        :param price: 주문단가
        :param hoga: 거래구분
        :param order_no: 원주문번호
        :return: 에러코드
        ex) 시장가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 0, “03”, “”);
        """
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def get_chejan_data(self, fid):
        """
        체결잔고 데이터 반환
        :param fid:  체결잔고 아이템
        :return: 수신 데이터
        """
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203)) # 주문번호
        print(self.get_chejan_data(302))  # 종목명
        print(self.get_chejan_data(900))  # 주문수량
        print(self.get_chejan_data(901))  # 주문가격

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2': self.remained_data = True
        else: self.remained_data = False

        if rqname == "opt10081_req": self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req": self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req": self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '': strip_data = '0'

        format_data = format(int(float(strip_data)), ",")  # 수정 부분
        if data.startswith('-'): format_data = '-' + format_data
        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '': strip_data = '0'
        if strip_data.startswith('.'):  strip_data = '0' + strip_data
        if data.startswith('-'): strip_data = '-' + strip_data
        return strip_data

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def _opt10081(self, rqname, trcode):
        """
        주식 일봉 차트 조회 요청
        :param rqname:  레코드명
        :param trcode:  Tran 이름
        :return:
        """
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._get_comm_data(trcode, rqname, i, "일자")
            open = self._get_comm_data(trcode, rqname, i, "시가")
            high = self._get_comm_data(trcode, rqname, i, "고가")
            low = self._get_comm_data(trcode, rqname, i, "저가")
            close = self._get_comm_data(trcode, rqname, i, "현재가")
            volume = self._get_comm_data(trcode, rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
        return self.ohlcv['close']



    def _opw00018(self, rqname, trcode):
        """
        계좌 평가 잔고 내역 요청
        :param rqname: 레코드명
        :param trcode: 거래코드
        :return:
        최대 20개 종목
        """
        # single data
        total_purchase_price = self._get_comm_data(trcode, rqname, 0, "총매입금액")
        total_eval_price = self._get_comm_data(trcode, rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
        total_earning_rate = self._get_comm_data(trcode,rqname, 0, "총수익률(%)")
        estimated_deposit = self._get_comm_data(trcode,rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(kiwoom.change_format(total_purchase_price))  # 총매입금액
        self.opw00018_output['single'].append(kiwoom.change_format(total_eval_price))      # 총평가금액
        self.opw00018_output['single'].append(kiwoom.change_format(total_eval_profit_loss_price))  # 총평가손익금액

        total_earning_rate = kiwoom.change_format(total_earning_rate)   # 총수익률

        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100   # 모의투자에서는 소숫점 표현으로 변환 필수, 실거래 서버는 소숫점 변환
            total_earning_rate = str(total_earning_rate)           # %로 표현, 문자열로 변환

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
            purchase_price = self._get_comm_data(trcode, rqname, i, "매입가")
            current_price = self._get_comm_data(trcode, rqname, i, "현재가")
            eval_profit_loss_price = self._get_comm_data(trcode, rqname, i, "평가손익")
            earning_rate = self._get_comm_data(trcode, rqname, i, "수익률(%)")
            quantity = kiwoom.change_format(quantity)
            purchase_price = kiwoom.change_format(purchase_price)
            current_price = kiwoom.change_format(current_price)
            eval_profit_loss_price = kiwoom.change_format(eval_profit_loss_price)
            earning_rate = kiwoom.change_format2(earning_rate)
            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price, eval_profit_loss_price,
                                                  earning_rate])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = kiwoom()
    kiwoom.comm_connect()

    account_num = kiwoom.get_login_info("ACCNO")
    account_num = account_num.split(";")[0]
    kiwoom.set_input_value("계좌번호",account_num)
    kiwoom.comm_rq_data("opw00018_req","opt100081",0,"2000")
    print(kiwoom.opw00018_output['single'])
    print(kiwoom.opw00018_output['multi'])


