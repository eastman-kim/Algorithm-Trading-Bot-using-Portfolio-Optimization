![screenshot](https://github.com/eastman-kim/Algorithm-Trading-Bot-using-Portfolio-Optimization/blob/master/img/screenshot.jpg)
# Optimus Prime V2 Beta (2020.10.05 - )

## Algorithm Trading Bot using Portfolio Optimization Theories
- Asset Selection: Sector-neutral Portfolio (Total 30 assets, z-score standardization)
- Portfolio Construction: Minimum Volatility Portfolio
- Portfolio Optimization : Rebalancing (currently only including commissions and tax, bid-ask spread will be added soon)

## How to Use?
- Open Optimus Prime and click 'Create Sector-neutral Portfolio'
- Then, click 'Calculate Calculate Optimal Weights' 
- 'Send an initial order' to purchase assets using the weights above
- Automatically 'Rebalance' the portfolio on the regular basis considering transaction costs
- Compare the result to the benchmark with a visualized graph

## Dev. Environment
- Anaconda3-4.3.0.1 32bit (Python 3.7, PyQt5.6)
- Windows 10
- requirements.txt
