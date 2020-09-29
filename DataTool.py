import pandas as pd
from datetime import datetime, timedelta
import pymysql


class DataTool:
    def __init__(self, code):
        self.item_code = code
        self.start, self.end = self.get_date()

    @staticmethod
    def get_merged_df(item_list):
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
        sql = "SELECT date,close as {table} FROM {table}_{date}".format(table=item_list[0],
                                                                        date=datetime.strftime(datetime.today(), '%Y%m%d'))
        df = pd.read_sql(sql, db)
        # from second item
        for item in item_list[1:]:
            sql = "SELECT date,close as {table} FROM {table}_{date}".format(table=item,
                                                                            date=datetime.strftime(datetime.today(), '%Y%m%d'))
            add_df = pd.read_sql(sql, db)
            df = df.merge(add_df, on='date')

        col_names = ['date'] + item_list
        df.columns = col_names
        print("Successfully merged")
        return df.set_index('date')





