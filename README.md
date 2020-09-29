![Image](../blob/master/OptimusPrime.png?raw=true)

## Algorithm Trading Bot using Portfolio Optimization Theories
- Asset Selection: Random 10 assets (will be updated soon)
- Portfolio Construction: Minimum Volatility
- Portfolio Optimization : Rebalancing (now transaction cost only includes only commission, will be updated soon)

## How to Use?
- Choose n number of assets you want and import 1-year price data
- Calculate optimal weights between assets and build a portfolio considering the minimum volatility
- Send an initial order to purchase assets using the weights above
- Rebalance the portfolio weights on the regular basis

## Dev. Environment
- Anaconda3-4.3.0.1 32bit (Python 3.7, PyQt5.6)
- Windows 10
- Other requirements
      - requests, traceback, BeautifulSoup, datetime,
      - pymysql, sqlalchemy, glob, time, calendar
