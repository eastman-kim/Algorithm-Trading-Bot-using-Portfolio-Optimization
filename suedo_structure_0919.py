class Body():
    """
    ### 기본 kiwoom api method
        입력 데이터 설정 : SetInputValue
        TR을 서버로 전송 : CommRqData
        이벤트 수신 알림 : OnReceiveTrData
        수신 데이터 Get  : CommGetData

    ### 필요한 PyQt
        버튼      : QPushButton("글자", self) -> .clicked.connect(connect 처리 method)
        결과보고창 : QTextEdit(self) -> append 로 글 입력
    ======================================================================================

    # 개요
    # Stock Selection
        pass

    # PyQt5 Widget(Update button 2개, QText 1개)

        # Weight Calculation(Update)

            ## Individual stock price change(historical mean & variance)
                ### get data
                    new_data = Naver finance crawled data up to today
                    return [pandas(new_data).mean, pandas(new_data).sd]

            ## Compute optimal weight by MC simulation
                return [optimal weight_updated]

        # Rebalancing(Update)   # 장중 아닐때 실행 하면 error 남

            ## Current NAV(평가액) lookup TR
                ### curr_nav = CommGetData()    #개발 3일차 읽어봐야함
                                                #method 로 만들어야함! 재사용

            ## Individual Stocks Current Price
                ### curr_nav = CommGetData()    #개발 3일차 읽어봐야함
    
            ## Buy Sell amount Calculation
                ### using ndarray
                    ndarray_individual_optimal_amount = curr_nav*[optimal weight_updated]/[individual_current_price]
                    diff(optimal, current)%1    # 자잘한 차액은 예비 금액 1억에서 차감 예정

            ## Buy Sell Order TR
                ### Sell
                    개발 2일차 읽어봐야함
                ### Buy
                    sell 해서 받은 돈으로 buy

        # Result shown in QTextEdit()
            ### 표시될 정보
                MPT weight

                전체 평가액(이거 다 넣으려면 QtTable 넣어야겠는데? 일단 평가액만 넣는걸로 시작하자)
                    종목이름
                    종목번호
                    종목별 보유 주식수

            ### curr_nav 다시 불러서 사용
            ### QTextEdit 인스턴스에 .append()
                    

    """
    # Class variable
    
    
    # __init__ instance variable
    
    
    # methods


    #Objective
