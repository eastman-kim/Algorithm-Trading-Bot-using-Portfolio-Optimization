import calendar
import numpy as np
import pandas as pd
from datetime import datetime
import pymysql
from Kiwoom import *


class PortfolioOptimizer:
    def __init__(self, code_list):
        self.code_list = code_list
        self.merged_df = self.get_merged_df()
        self.price_df = self.get_price_df()
        self.name_df = self.get_name_df()
        self.weight_df = self.opt_weight_df()
        self.init_buy_list = self.create_buy_list()

    def get_merged_df(self):
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
        sql = "SELECT date,close as '{item_code}' FROM {item_code}_{date}".format(item_code=self.code_list[0],
                                                                                  date=datetime.strftime(
                                                                                      datetime.today(), '%Y%m%d'))
        df = pd.read_sql(sql, db)
        # from second item
        for item in self.code_list[1:]:
            sql = "SELECT date,close as '{item_code}' FROM {item_code}_{date}".format(item_code=item,
                                                                                      date=datetime.strftime(
                                                                                          datetime.today(), '%Y%m%d'))
            add_df = pd.read_sql(sql, db)
            df = df.merge(add_df, on='date')

        col_names = ['date'] + self.code_list
        df.columns = col_names
        print("succeeded")
        return df.set_index('date')[:253]  # 1-year data

    def get_name_df(self):
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
        for code in self.code_list:
            df = pd.concat([df, code_df.loc[code_df['code'] == code]])
        name_df = df.set_index('code')
        print("succeeded")
        return name_df

    def get_price_df(self):
        print("****** Getting today's close price ******")
        price_df = self.merged_df[:1].T
        price_df.columns = ['price']
        print("succeeded")
        return price_df

    def opt_weight_df(self, num_sim = 1000):

        """
    Get optimal weights in the Monte-Carlo approach.
    You can choose the number of simulation running the different combination of weights on each asset. (Default:10,000)
    Minimum volatility is priortized to build our portfolio.
    This function returns the optimal weights of the portfolio in a dataframe.


        """
        # np.random.seed(909)
        print("****** Calculating the optimal weights for the portfolio ******")
        n_items = self.merged_df.shape[1]
        rets = self.merged_df.pct_change()
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
        for code in self.code_list:
            col_names.append(code)
        cols = ['returns', 'stdev', 'sharpe'] + col_names
        res_df = pd.DataFrame(res.T, columns=cols)

        # locate position of portfolio with minimum standard deviation
        min_vol = res_df.iloc[res_df['stdev'].idxmin()]

        opt_weights = pd.DataFrame(min_vol[3:])
        opt_weights.columns = ['opt_wgt']
        print("succeeded")
        return opt_weights

    def create_buy_list(self):
        # concat weights_df, price_df, code_df
        print("****** Creating my initial buy list ******")
        name_df = self.name_df
        price_df = self.price_df
        weight_df = self.weight_df
        new_df = pd.concat([name_df, price_df, weight_df], axis=1)

        init_inv = 200000  # initial investment: 200M won
        new_df['inv amount'] = init_inv * new_df['opt_wgt']  # investment amount per asset
        new_df['quantity'] = round(new_df['inv amount'] / new_df['price'], 0).astype(int)  # quantity round to int
        print("succeeded")
        return new_df

    def rebalance(self):
        """
            Rebalance the portfolio on the regular basis.(on the last day of the current month)
            Currently it proceed when the button is clicked for the debugging purpose.
            This function send buy/sell orders to Kiwoom Open API to proceed corresponding transaction.
        """
        df = kiwoom.get_current_info()
        opt_df = self.init_buy_list[['code', 'opt_wgt']]
        df = df.merge(opt_df, on='name')

        today = datetime.today()
        year, month = today.year, today.month
        last_day = calendar.monthrange(year, month)[1]
        if today == today:

            df['cur_nav'] = df['current_price'].str.replace(',', '').astype(int) * df['quantity'].astype(int)
            df['cur_wgt'] = df['cur_nav'] / sum(df['cur_nav'])

            # the difference between current weights and initial optimal weights
            df['wgt_diff'] = df['cur_wgt'] - df['opt_wgt']

            # add column name 'action'
            df.loc[df['wgt_diff'] > 0, 'action'] = 'sell'
            df.loc[df['wgt_diff'] < 0, 'action'] = 'buy'

            # add buy/sell amounts and quantity
            df['buy/sell amount'] = abs(df['wgt_diff'] * sum(df['cur_nav']))
            df['buy/sell quantity'] = df['buy/sell amount'] / df['current_price'].str.replace(',', '').astype(int)

            # final decision considering transaction cost(commission 0.35%)
            df.loc[df['buy/sell amount'] > df['cur_nav']*0.0035, 'decision'] = 'do'
            df.loc[df['buy/sell amount'] < df['cur_nav']*0.0035, 'decision'] = 'stay'

            # buy and sell list
            buy_list = df.loc[(df['action'] == 'buy') & (df['decision'] == 'do')]
            buy_list = buy_list[['name', 'code', 'action', 'buy/sell amount', 'buy/sell quantity']]
            print("There are {} assets needed to be bought".format(len(buy_list)))
            for i in range(len(buy_list)):
                print(i+1, buy_list.iloc[i][0], 'buy', int(buy_list.iloc[i][4]))

            sell_list = df.loc[(df['action'] == 'sell') & (df['decision'] == 'do')]
            sell_list = sell_list[['name', 'code', 'action', 'buy/sell amount', 'buy/sell quantity']]
            print(sell_list)
            print("There are {} assets needed to be sold".format(len(sell_list)))
            for i in range(len(sell_list)):
                print(i+1, sell_list.iloc[i][0], 'sell', int(sell_list.iloc[i][4]))
            print()

            print("****** Rebalancing my portfolio ******")
            # order according to each list
            for i in range(len(buy_list)):
                if int(buy_list.iloc[i][4]) != 0:
                    kiwoom.send_order('order_rq', '0101', kiwoom.account_number, 1,
                                      str(buy_list.iloc[i][1]), int(buy_list.iloc[i][4]), 0, '03', '', buy_list.iloc[i][0])
            for j in range(len(sell_list)):
                if int(sell_list.iloc[j][4]) != 0:
                    kiwoom.send_order('order_rq', '0101', kiwoom.account_number, 2,  # 신규매도
                                      str(sell_list.iloc[j][1]), int(sell_list.iloc[j][4]), 0, '03', '', sell_list.iloc[j][0])
            print()

            # check if rebalance has succeeded
            print("succeeded")

if __name__ == "__main__":
    kiwoom = kiwoom()
    kiwoom.comm_connect()
    code_list = ['039490','005380']
    po = PortfolioOptimizer(code_list)
    po.send_initial_order()
