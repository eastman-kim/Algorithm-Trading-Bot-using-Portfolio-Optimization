import calendar
from GetStockPrice import *
from kiwoom import *

MARKET_KOSPI = 0
MARKET_KOSDAQ = 10


class PortfolioOptimizer:
    def __init__(self, items):
        self.items = items
        self.code_df = self.get_company_code_df()
        self.merged_df = self.get_merged_df()
        self.price_df = self.get_price_df()
        self.weight_df = self.opt_weight_df(self.merged_df)
        self.init_buy_list = self.create_buy_list()

    def get_company_code_df(self):
        """
        Get company codes from KRX(Korea Exchange)
        """
        code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13',
                               header=0)[0]
        # convert into 6 digits code
        code_df['종목코드'] = code_df['종목코드'].map('{:06d}'.format)
        # remove unnecessary columns
        code_df = code_df[['회사명', '종목코드']]
        # change Korean to English
        code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

        d = dict()
        for item in self.items:
            for i in range(len(code_df)):
                if code_df.iloc[i][0] == item:
                    d[code_df.iloc[i][0]] = code_df.iloc[i][1]
        code_df = pd.DataFrame(d, index=['code']).T
        print("SUCCESS: get company code")
        return code_df

    def get_merged_df(self):
        merged_df = GetStockPrice.get_merged_df(self.items)
        return merged_df

    def get_price_df(self):
        price_df = self.merged_df[-1:].T
        price_df.columns = ['price']
        price_df = pd.DataFrame(price_df)
        print("SUCCESS: get today's close price")
        return price_df

    @staticmethod
    def opt_weight_df(df, num_sim=10000):

        """
    Get optimal weights in the Monte-Carlo approach.
    You can choose the number of simulation running the different combination of weights on each asset. (Default:10,000)
    Minimum volatility is priortized to build our portfolio.
    This function returns the optimal weights of the portfolio in a dataframe.


        """

        num_sim = num_sim
        item_list = df.columns
        n_items = df.shape[1]
        rets = df.pct_change()
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
        for item in item_list:
            col_names.append(item)
        cols = ['returns', 'stdev', 'sharpe'] + col_names
        res_df = pd.DataFrame(res.T, columns=cols)

        # locate position of portfolio with minimum standard deviation
        min_vol = res_df.iloc[res_df['stdev'].idxmin()]

        opt_weights = pd.DataFrame(min_vol[3:])
        opt_weights.columns = ['opt_wgt']
        print("SUCCESS: get optimal weights")
        return opt_weights

    def create_buy_list(self):
        # concat weights_df, price_df, code_df
        print("****** Creating my initial buy list ******")
        code_df = self.code_df
        price_df = self.price_df
        weight_df = self.weight_df
        new_df = pd.concat([code_df, price_df, weight_df], axis=1)

        init_inv = 200000000  # initial investment: 2 billion won
        new_df['inv amount'] = init_inv * new_df['weights']  # investment amount per asset
        new_df['quantity'] = round(new_df['inv amount'] / new_df['price'], 0).astype(int)  # quantity round to int
        print("Successfully created my initial buy list")
        return new_df

    def initial_order(self):
        kiwoom.set_input_value("계좌번호", kiwoom.account_number)
        init_buy_list = self.init_buy_list
        for i in range(len(init_buy_list)):
            kiwoom.bid_mrk_order(init_buy_list.iloc[i][1], init_buy_list.iloc[i][5])  # 1 for code, 5 for quantity

    def rebalance(self):
        """
            Rebalance the portfolio on the regular basis.(on the last day of the current month)
            Currently it proceed when the button is clicked for the debugging purpose.
            This function send buy/sell orders to Kiwoom Open API to proceed corresponding transaction.
        """
        df = kiwoom.opw00018_output['multi'].set_index('name')
        opt_df = self.init_buy_list[['code', 'opt_wgt']]
        df = pd.concat([df, opt_df], axis=1)

        today = datetime.today()
        year, month = today.year, today.month
        last_day = calendar.monthrange(year, month)[1]
        if today == last_day:
            df['cur_nav'] = df['current_price'] * df['quantity']
            df['cur_wgt'] = df['cur_nav'] / sum(df['cur_nav'])

            # the difference between current weights and initial optimal weights
            df['wgt_diff'] = df['cur_wgt'] - df['opt_wgt']

            # add column name 'action'
            df.loc[df['wgt_diff'] >= 0, 'action'] = 'buy'
            df.loc[df['wgt_diff'] < 0, 'action'] = 'sell'

            # add buy/sell amounts and quantity
            df['buy/sell amount'] = abs(df['wgt_diff'] * sum(df['cur_nav']))
            df['buy/sell quantity'] = df['buy/sell amount'] / df['current_price']

            # final decision considering transaction cost(commission 0.35%)
            df.loc[df['buy/sell amount'] > df['cur_nav']*0.0035, 'decision'] = 'do'
            df.loc[df['buy/sell amount'] < df['cur_nav']*0.0035, 'decision'] = 'stay'

            # buy and sell list
            buy_list = df[df['decision'] == 'do']
            print("There are {} assets needed to be bought".format(len(buy_list)))
            sell_list = df[df['decision'] == 'stay']
            print("There are {} assets needed to be sold".format(len(sell_list)))
            print()
            # order according to the lists
            for i in range(len(buy_list)):
                kiwoom.bid_mrk_order(buy_list.iloc[i]['code 있는 컬럼'], buy_list.iloc[i]['buy/sell quantity 있는 컬럼'])

            for j in range(len(sell_list)):
                kiwoom.bid_mrk_order(buy_list.iloc[j]['code 있는 컬럼'], buy_list.iloc[j]['buy/sell quantity 있는 컬럼'])

        # check if rebalance has succeeded
        print(kiwoom.opw00018_output['multi'])
