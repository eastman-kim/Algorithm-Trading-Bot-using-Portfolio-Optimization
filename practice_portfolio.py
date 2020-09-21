# 기본 portfolio(가정) (dataframe)
# 종목갯수 1

# df
# 종목                  |   키움증권
# -----------------------------------------
# 종목코드               |   "039490"
# 기존 주당 보유 갯수     |     "10"
# 기존 가격 정보         |  "111"(가짜 가격)

import pandas as pd
import numpy as np

class practice_portfolio:
    list1 = ["키움증권", "039490", "10", "111"]
    list2 = ["삼성전자", "005930", "10", "222"]

    df_practice = pd.DataFrame([list1, list2],columns=["종목","종목번호","(기존)보유갯수","(기존)주가"])

