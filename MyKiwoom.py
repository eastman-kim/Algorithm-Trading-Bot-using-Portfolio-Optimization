# # 앞으로 정할 portfolio 정보
# from practice_portfolio import *
# ppf = practice_portfolio.df_practice


# import sys
# import pandas as pd
# from PyQt5.QtWidgets import *
# from PyQt5.QtGui import *
# from PyQt5.QAxContainer import *
# import time

# # 단독 실행시 QApplication 생성해주고 돌려야함

# class MyKiwoom():
    
#     def __init__(self,main_widget):
        
#         self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
#         self.main_widget = main_widget

#         print("up to MyKiwoom instance")  #debug

#         #자동 로그인
#         self.ki_login() #off when debugging

#         #자동 개별 종목 현재가 정보
#         # self.price_enumer() #arg로 porfolio 종목 list 줘야함

#     #로그인 method
#     def ki_login(self):

#         #kiwoom widget 프로그램 import
#         self.kiwoom.dynamicCall("CommConnect()")
#         self.kiwoom.OnEventConnect.connect(self.event_connect)  #connect 가 arg 알아서 줌

#     def event_connect(self, err_code):
#         if err_code == 0:
#             self.main_widget.text_edit.append("logged in")    #debug 할때만 꺼놓음
#             print("logged in")    #debug
#         else:
#             print("not logged in")
#     #개별 종목 현재가 list 만들기
#     def price_enumer(self):
#         codes = ppf.iloc[:,1].tolist()
#         prices = []

#         for c in codes:
#             prices.append(self.fetch_single_price(c))

#         # 다른 method 에서도 쓸꺼니까 Kiwoom.prices 로 만들어 놓는다
#         self.prices = prices
#         print("up to price_enumer, prices = ", prices[0])  #debug
            
#     #종목 1개 현재가 검색
#     def fetch_single_price(self, code):
#         self.temp_price = None

#         #API 요청 -> 정보회수
#         #종목 특정 해주는 요청 보내기
#         self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
#         print("up to fetch set input value")    #debug
#         #TR 특정해주는 요청 보내기
#         self.kiwoom.dynamicCall("CommRqData(QString,QString,int,QString)","opt10001_req","opt10001",0,"0101")
#         print("up to fetch commrq")    #debug
#         #Recieve Event 까지 wait -> 현재가 정보 fetch
#         self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)
#         print("up to fetch final")    #debug
        
#         # print(self.kiwoom==None)    #debug
#         return self.temp_price

#     def receive_trdata(self, screen_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
#         if rqname == "opt10001_req":
#             self.temp_price = self.kiwoom.dynamicCall("CommGetData(QString,QString,QString,int,QString)",trcode,"",rqname,0,"현재가")
#             print(self.temp_price+"\n up to receive_trdata") #debug

#             #debug 해보니까 strip 엄청 해야함! 찍히기는 한다 근데 넘어갈때 None으로 넘어가는거 고쳐야함
#         else:
#             print("receive_trdata not working")


# # app = QApplication(sys.argv)    #debug
# # test1 = MyKiwoom(True)    #debug