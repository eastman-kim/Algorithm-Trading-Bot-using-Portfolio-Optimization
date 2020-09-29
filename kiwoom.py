from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PortfolioOptimizer import *
import sys
from PyQt5.QtWidgets import *
import time
from sqlalchemy import create_engine


class kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

        self.order_type_dict = {1: "신규매수", 2: "신규매도", 3: "매수취소",
                                4: "매도취소", 5: "매수정정", 6: "매도정정"}
        self.order_price_dict = {"00": "지정가", "03": "시장가", "05": "조건부지정가", "06": "최유리지정가",
                                 "07": "최우선지정가", "10": "지정가IOC", "13": "시장가IOC", "16": "최유리IOC",
                                 "20": "지정가FOK", "23": "시장가FOK", "26": "최유리FOK", "61": "장전시간외종가",
                                 "62": "시간외단일가", "81": "장후시간외종가"}
        self.gubun_dict = {0: "주문체결통보", 1: "잔고통보", 3: "특이신호"}
        self.msg_cnt = [0, 0, 0]

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
        print("****** Logging in ****** ")
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

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

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

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no, name):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        self.chejan_loop = QEventLoop()
        print("System>>> '{} {}주 {}로 {} 주문중...'".format(
            name, quantity, self.order_price_dict[hoga], self.order_type_dict[int(order_type)]))
        print("System>>> Order sent and waitting for first call back...")
        self.chejan_loop.exec_()

    """
    def bid_mrk_order(self, stock_code, quantity):
        self.send_order("order_req", "0101", self.account_number, "1", stock_code, quantity, 0, "03", "")

    def ask_mrk_order(self, stock_code, quantity):
        self.send_order("order_req", "0101", self.account_number, "2", stock_code, quantity, 0, "03", "")
    """

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
        self.chejan_gubun = int(gubun)
        self.msg_cnt[self.chejan_gubun] += 1

        print("System>>> total of {} message about {} received"
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

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2': self.remained_data = True
        else: self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

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

    def get_current_info(self):
        self.set_input_value("계좌번호", self.account_number)
        self.reset_opw00018_output()
        self.comm_rq_data("opw00018_req", "opw00018", 0, "0101")
        ret = pd.DataFrame(self.opw00018_output["multi"], columns=['name', 'quantity', 'purchase_price',
                                                                   'current_price', 'eval_price', 'earning_rate'])
        return ret

    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = kiwoom.change_format(d2_deposit)

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

    @staticmethod
    def get_date():
        """
        return a date 1-year away from today
        """
        start = datetime.strftime(datetime.today() - timedelta(days=365), '%Y-%m-%d')
        end = datetime.strftime(datetime.today(), '%Y-%m-%d')
        return start

    def get_opt10081_save_data(self, code, start):
        print('start get ohlcv')
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(0.2)
        print(self.ohlcv)
        print('creating df')
        return pd.DataFrame(self.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                          index=self.ohlcv['date'])
        """
        print('got data and saving to MySQL')
        # save to mysql
        engine = create_engine("mysql+pymysql://root:" + "root" + "@localhost:3306/stock_price?charset=utf8",
                               encoding='utf-8')
        conn = engine.connect()
        df.to_sql(name=('{code}_{today}'.format(code=code,
                                                today=datetime.strftime(datetime.today(), '%Y%m%d')).lower()),
                  con=engine, if_exists='replace', index=False)
        conn.close()
        print('Successfully Saved in MySQL Server')
        print()
        """

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

    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]
    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
