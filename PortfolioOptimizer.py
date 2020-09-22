# coding: utf-8
import pandas as pd
import numpy as np
from kiwoom import *

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10


class PortfolioOptimizer:
    def __init__(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        self.account_number = account_number.split(';')[0]

    def opt_weight(self, num_sim=10000):

        """
    Get optimal weights in the Monte-Carlo approach.
    You can choose the number of simulation running the different combination of weights on each asset. (Default:10,000)
    Minimum volatility is priortized to build our portfolio.
    This function returns the optimal weights of the portfolio in a dataframe.

    주의사항
    1) 자산 10개용. 자산 갯수 변경 시 res_df item_list 수정요함.

        """

        self.kiwoom.set_input_value("계좌번호", self.account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        df = self.opw00018_output['multi']['close'] # 수정 필요. 현재가로.

        num_sim = num_sim
        item_list = df.columns
        n_items = df.shape[0]
        rets = df.pct_change()
        mean_daily_rets = rets.mean()
        cov_matrix = rets.cov()
        res = np.zeros((3 + n_items,num_sim))  # 3 for returns, std, and sharpe ratio

        # get optimal weights in Monte-Carlo approach
        for i in range(num_sim):
            weights = np.random.random(n_items)
            weights = weights/sum(weights)

            # annualized returns and standard deviation
            prf_rets = np.sum(mean_daily_rets*weights*252)
            prf_std = np.sqrt(weights.T@(cov_matrix@weights))*np.sqrt(252)

            # returns
            res[0, i] = prf_rets
            # volatility
            res[1, i] = prf_std
            # sharpe ratio(simple ver)
            res[2, i] = res[0, i]/res[1, i]

            #
            for j in range(len(weights)):
                res[j+3, i] = weights[j]

        res_df = pd.DataFrame(res.T, columns=['returns','stdev','sharpe',
                                              item_list[0], item_list[1], item_list[2],
                                              item_list[3], item_list[4], item_list[5],
                                              item_list[6], item_list[7], item_list[8],
                                              item_list[9]])

        # locate position of portfolio with highest Sharpe Ratio
        max_sharpe = res_df.iloc[res_df['sharpe'].idxmax()]
        # locate position of portfolio with minimum standard deviation
        min_vol = res_df.iloc[res_df['stdev'].idxmin()]

        self.opt_wgts = pd.DataFrame(min_vol[3:], columns=['opt_wgt'])
        return 1

    def rebalance(self):

        """
            Rebalance the portfolio on the regular basis.
            Currently it proceed when the button is clicked for the debugging purpose.
            This function send buy/sell orders to Kiwoom Open API to proceed corresponding transaction.

            데이터 타입 확인해서 필요시 int, float으로 변경
            데이터 컬럼: 종목, 종목코드, 보유량, 현재가
        """
        kiwoom.reset_opw00018_output()
        kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        df = kiwoom.opw00018_output['multi']

        # rebalance at the end of the month
        # import calender
        # from datetime import datetime
        # today = datetime.today()
        # year, month = today.year, today.month
        # if today == last_day calender.monthrange(year,month)[1]:
        #    run below

        df['cur_nav'] = current_price * quantity
        df['cur_wgt'] = cur_nav / sum(cur_nav)
        df = pd.concat([df, self.opt_wgts], axis=1)
        df['wgt_diff'] = cur_wgt - opt_wgt
        df['buy sell amount'] = df['wgt_diff'] * sum(cur_nav)
        df['buy sell shares'] = df['buy sell amount'] / now_price

        # transaction cost(commission 0.35%)
        sell_list = df[(abs(df['buy sell amount']) > df['cur_nav'] * 0.0035) and (df['buy sell shares'] > 0)]
        buy_list = df[(abs(df['buy sell amount']) > df['cur_nav'] * 0.0035) and (df['buy sell shares'] < 0)]

        return 1


    def update_buy_list(self, buy_list):
        f = open("buy_list.txt", "wt")
        for code in buy_list:
            f.writelines("매수;", code, ";시장가;10;0;매수전")
        f.close()

    def run(self):
        buy_list = []
        num = 999 #len(self.kosdaq_codes)

        for i, code in enumerate(self.kosdaq_codes):
            print(i, '/', num)
            if self.check_speedy_rising_volume(code):
                buy_list.append(code)

        self.update_buy_list(buy_list)

