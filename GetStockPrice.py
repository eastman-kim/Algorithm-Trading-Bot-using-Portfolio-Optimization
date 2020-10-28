import pandas as pd
import numpy as np
import time
import requests, json

# momentum, sector_df will be added

@staticmethod
def get_sector_df():
    """
    Get sector data from WiseIndex
    """
    df = pd.DataFrame(columns=["IDX_CD", "IDX_NM_KOR", "ALL_MKT_VAL", "CMP_CD", "CMP_KOR", "MKT_VAL", "WGT",
                               "S_WGT", "CAL_WGT", "SEC_CD", "SEC_NM_KOR", "SEQ", "TOP60", "APT_SHR_CNT"])
    sector_code = ['G25', 'G35', 'G50', 'G40', 'G10', 'G20', 'G55', 'G30', 'G15', 'G45']

    for code in sector_code:
        print("****** Crawling Sector Code {} ****** ".format(code))
        url = 'http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt=20200929&sec_cd={}'.format(code)
        result = requests.get(url)
        data = json.loads(result.text)['list']

        for i in range(len(data)):
            df.loc[len(df)] = {
                "IDX_CD": data[i]['IDX_CD'],
                "IDX_NM_KOR": data[i]['IDX_NM_KOR'],
                "ALL_MKT_VAL": data[i]['ALL_MKT_VAL'],
                "CMP_CD": data[i]['CMP_CD'],
                "CMP_KOR": data[i]['CMP_KOR'],
                "MKT_VAL": data[i]['MKT_VAL'],
                "WGT": data[i]['WGT'],
                "S_WGT": data[i]['S_WGT'],
                "CAL_WGT": data[i]['CAL_WGT'],
                "SEC_CD": data[i]['SEC_CD'],
                "SEC_NM_KOR": data[i]['SEC_NM_KOR'],
                "SEQ": data[i]['SEQ'],
                "TOP60": data[i]['TOP60'],
                "APT_SHR_CNT": data[i]['APT_SHR_CNT']}
        print("Completed Crawling {}".format(code))
        df = df.append(df)
        time.sleep(2)
    print("Successfully Bound All DataFrames!")
    return df
