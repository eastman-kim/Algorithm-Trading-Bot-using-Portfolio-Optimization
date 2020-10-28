import calendar
import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime
import time
import pymysql
from sqlalchemy import create_engine
from Kiwoom import *


class PortfolioOptimizer:
    def __init__(self):
        self.kiwoom = Kiwoom()

    @staticmethod
    def get_merged_df(code_list):
        print("****** Merging DataFrames ******")
        # mysql server credentials
        host_name = "localhost"
        username = "root"
        password = "root"
        database_name = "stock_price"

        db = pymysql.connect(
            host=host_name,  # DATABASE_HOST
            port=3306,
            user=username,  # DATABASE_USERNAME
            passwd=password,  # DATABASE_PASSWORD
            db=database_name,  # DATABASE_NAME
            charset='utf8'
        )

        # default df(first item) for merging all data
        sql = "SELECT date,close as '{item_code}' FROM {item_code}_{date}".format(item_code=code_list[0],
                                                                                  date=datetime.strftime(
                                                                                      datetime.today(), '%Y%m%d'))
        df = pd.read_sql(sql, db)
        # from second item
        for item in code_list[1:]:
            sql = "SELECT date,close as '{item_code}' FROM {item_code}_{date}".format(item_code=item,
                                                                                      date=datetime.strftime(
                                                                                          datetime.today(), '%Y%m%d'))
            add_df = pd.read_sql(sql, db)
            df = df.merge(add_df, on='date')

        col_names = ['date'] + code_list
        df.columns = col_names
        print("succeeded")
        return df.set_index('date')[:757]  # 3-year data

    @staticmethod
    def get_name_df(code_list):
        """
        Get item names from KRX(Korea Exchange)
        """
        print("****** Getting item names ******")
        code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13',
                               header=0)[0]
        # convert into 6 digits code
        code_df['종목코드'] = code_df['종목코드'].map('{:06d}'.format)
        # remove unnecessary columns
        code_df = code_df[['회사명', '종목코드']]
        # change Korean to English
        code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

        df = pd.DataFrame()
        for code in code_list:
            df = pd.concat([df, code_df.loc[code_df['code'] == code]])
        name_df = df.set_index('code')
        print("succeeded")
        return name_df

    @staticmethod
    def get_price_df(code_list, merged_df):
        print("****** Getting today's close price ******")
        price_df = merged_df[:1].T
        price_df.columns = ['price']
        print("succeeded")
        return price_df

    @staticmethod
    def opt_weight_df(code_list, merged_df, num_sim=1000):

        """
        Get optimal weights in the Monte-Carlo approach.
        You can choose the number of simulation running the different combination of weights on each asset. (Default:10,000)
        This function returns the optimal weights of the portfolio considering the minimum volatility.
        """
        print("****** Calculating the optimal weights for the portfolio ******")
        n_items = merged_df.shape[1]
        rets = merged_df.pct_change()
        mean_daily_rets = rets.mean()
        cov_matrix = rets.cov()
        res = np.zeros((3 + n_items, num_sim))  # 3 for returns, std, and sharpe ratio

        # get optimal weights in Monte-Carlo approach
        for i in range(num_sim):
            weights = np.random.random(n_items)
            weights = weights / sum(weights)

            # annualized returns and standard deviation
            prf_rets = np.sum(mean_daily_rets * weights * 252)
            prf_std = np.sqrt(weights.T @ (cov_matrix @ weights)) * np.sqrt(252)

            # returns
            res[0, i] = prf_rets
            # volatility
            res[1, i] = prf_std
            # sharpe ratio(simple ver)
            res[2, i] = res[0, i] / res[1, i]

            #
            for j in range(len(weights)):
                res[j + 3, i] = weights[j]

        col_names = []
        for code in code_list:
            col_names.append(code)
        cols = ['returns', 'stdev', 'sharpe'] + col_names
        res_df = pd.DataFrame(res.T, columns=cols)

        # locate position of portfolio with minimum standard deviation
        min_vol = res_df.iloc[res_df['stdev'].idxmin()]

        opt_weights = pd.DataFrame(min_vol[3:])
        opt_weights.columns = ['opt_wgt']
        print("succeeded")
        return opt_weights

    @staticmethod
    def create_buy_list(name_df, price_df, weight_df):
        # concat weights_df, price_df, code_df
        print("****** Creating my initial buy list ******")
        new_df = pd.concat([name_df, price_df, weight_df], axis=1)

        init_inv = 2000000  # initial investment: 200M won
        new_df['inv amount'] = init_inv * new_df['opt_wgt']  # investment amount per asset
        new_df['quantity'] = round(new_df['inv amount'] / new_df['price'], 0).astype(int)  # quantity round to int
        new_df = new_df.reset_index()
        print("succeeded")

        # save to mysql
        engine = create_engine("mysql+pymysql://root:" + "root" + "@localhost:3306/stock_price?charset=utf8",
                               encoding='utf-8')
        conn = engine.connect()
        new_df.to_sql(name='init_buy_list', con=engine, if_exists='replace', index=True)
        conn.close()
        print('Successfully Saved in MySQL Server')

    def rebalance(self, df):
        """
            Rebalance the portfolio on the regular basis.(on the last day of the current month)
            Currently it proceed when the button is clicked for the debugging purpose.
            This function send buy/sell orders to Kiwoom Open API to proceed corresponding transaction.
        """
        # rebalance on the regular basis?
        # or rebalance when the weight difference is bigger than 5%

        # mysql server credentials
        host_name = "localhost"
        username = "root"
        password = "root"
        database_name = "stock_price"

        db = pymysql.connect(
            host=host_name,  # DATABASE_HOST
            port=3306,
            user=username,  # DATABASE_USERNAME
            passwd=password,  # DATABASE_PASSWORD
            db=database_name,  # DATABASE_NAME
            charset='utf8'
        )

        # default df(first item) for merging all data
        sql = "SELECT * FROM init_buy_list"
        opt_df = pd.read_sql(sql, db)
        opt_df = opt_df.set_index('index')
        opt_df = opt_df[['code', 'opt_wgt']]

        code_list = list(opt_df.code)
        name_df = self.get_name_df(code_list)
        code_name_df = opt_df.merge(name_df, on='code')

        df = code_name_df.merge(df, on='name')

        today = datetime.today()
        year, month = today.year, today.month
        last_day = calendar.monthrange(year, month)[1]
        if today == today:
            df['cur_nav'] = df['current_price'].str.replace(',', '').astype(int) * df['quantity'].astype(int)
            df['cur_wgt'] = df['cur_nav'] / sum(df['cur_nav'])

            # the difference between current weights and initial optimal weights
            df['wgt_diff'] = df['cur_wgt'] - df['opt_wgt']

            # add column name 'action', can change the range (0-3%)
            df.loc[df['wgt_diff'] > 0.00, 'action'] = 'sell'
            df.loc[df['wgt_diff'] < 0.00, 'action'] = 'buy'

            # add buy/sell amounts and quantity - transaction cost(commission 0.35%, tax 0.25%)
            df['buy/sell amount'] = abs(df['wgt_diff']) * df['cur_nav']
            df['buy/sell quantity'] = round(df['buy/sell amount'] / df['current_price'].str.replace(',', '').astype(int),0)

            # tc = (df['buy/sell amount'] * 0.0035 + df['buy/sell amount'] * 0.0025)
            # ask_bid_spread
            # tc + ask_bid_spread 보다 몇 퍼센트 커야 거래 진행?
            # df.loc[df['buy/sell amount'] * 0.01 > tc + ask_bid_price, 'decision'] = 'do'
            # df.loc[df['buy/sell amount'] * 0.01 < tc + ask_bid_price, 'decision'] = 'stay'

            # buy and sell list
            buy_list = df.loc[df['action'] == 'buy']
            buy_list = buy_list[['name', 'code', 'action', 'buy/sell amount', 'buy/sell quantity']]
            print("There are {} assets needed to be bought".format(len(buy_list)))
            for i in range(len(buy_list)):
                print(i+1, buy_list.iloc[i][0], 'buy', int(buy_list.iloc[i][4]))

            sell_list = df.loc[df['action'] == 'sell']
            sell_list = sell_list[['name', 'code', 'action', 'buy/sell amount', 'buy/sell quantity']]
            print("There are {} assets needed to be sold".format(len(sell_list)))
            for i in range(len(sell_list)):
                print(i+1, sell_list.iloc[i][0], 'sell', int(sell_list.iloc[i][4]))
            print()

            print("****** Rebalancing my portfolio ******")
            account_number = self.kiwoom.get_login_info("ACCNO")
            account_number = account_number.split(';')[0]
            self.kiwoom.set_input_value("계좌번호", account_number)

            # order according to each list
            for i in range(len(buy_list)):
                if int(buy_list.iloc[i][4]) != 0:
                    self.kiwoom.send_order('buy_order_rq', '0101', account_number, 1, buy_list.iloc[i][1],
                                           int(buy_list.iloc[i][4]), 0, '03', '', buy_list.iloc[i][0])

            for j in range(len(sell_list)):
                if int(sell_list.iloc[j][4]) != 0:
                    self.kiwoom.send_order('sell_order_rq', '0101', account_number, 2, sell_list.iloc[j][1],
                                           int(sell_list.iloc[j][4]), 0, '03', '', sell_list.iloc[j][0])
            print()

            # check if rebalance has succeeded
            print("succeeded")


