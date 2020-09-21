#!/usr/bin/env python
# coding: utf-8

# # 0. Environment Setting

# In[1]:


import os
import pandas as pd
import numpy as np
import requests, traceback
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import pymysql
from sqlalchemy import create_engine
import glob


# # Get Daily Stock Price from Naver Finance

# ### Importing Stock Price Data

# In[5]:


class get_stock_price:
    def __init__(self, item_name):
        self.item_name = item_name
        
    def get_date(self):
        self.start = datetime.strftime(datetime.today() - timedelta(days=365),'%Y-%m-%d')
        self.end = datetime.strftime(datetime.today() ,'%Y-%m-%d')
                
    def get_company_code(self):
        """
        Get company codes from KRX(Korea Exchange) 
        """
        code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]  
        # convert into 6 digits code
        code_df.종목코드 = code_df.종목코드.map('{:06d}'.format) 
        # remove unnecessary columns 
        code_df = code_df[['회사명', '종목코드']] 
        # change Korean to English
        code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})
        self.code = code_df.query("name=='{}'".format(self.item_name))['code'].to_string(index=False).lstrip()
        print('Item Code:',self.code)
        return self.code
    
    def get_last_page(self):
        """
        Get the last page of item 
        """
        url = 'http://finance.naver.com/item/sise_day.nhn?code='+ self.code
        result = requests.get(url) 
        soup = BeautifulSoup(result.text, 'html.parser')
        maxPage=soup.find_all("table",align="center") 
        lp = maxPage[0].find_all("td",class_="pgRR") 
        last_page = lp[0].a.get('href').rsplit('&')[1]
        last_page = last_page.split('=')[1]
        self.last_page = int(last_page)
        return self.last_page

    def parse_page(self, page):
        try:
            url = 'http://finance.naver.com/item/sise_day.nhn?code=' + self.code +'&page='+ str(page)
            result = requests.get(url)
            soup = BeautifulSoup(result.content, 'html.parser')
            df = pd.read_html(str(soup.find("table")), header=0)[0].dropna()   
            return df 
        except Exception as e:
            traceback.print_exc()
        return None
    
    def get_final_df(self):
        """
        Create a final dataset
        """
        final_df = None
        print('****** Start Crwaling ******')
        for page in range(1, self.last_page+1):
            _df = self.parse_page(page)
            _df_filtered = _df[_df['날짜'] >= self.start]
            print('Crawling page #{}'.format(page))
            if final_df is None:
                final_df = _df_filtered
            else:
                final_df = pd.concat([final_df, _df_filtered])
                
            if len(_df) > len(_df_filtered) :
                print('****** Crwaling Completed ******')
                break
        
        #change column names
        final_df = final_df.rename(columns= {'날짜': 'date', '종가': 'close', '전일비': 'diff',
                                             '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'}) 
        #change data type into int
        final_df[['close', 'diff', 'open', 'high', 'low', 'volume']] = final_df[['close', 'diff', 'open', 'high', 'low', 'volume']].astype(int) 
        #change data type into date
        final_df['date'] = pd.to_datetime(final_df['date']) 
        #sort
        final_df = final_df.sort_values(by=['date'], ascending=True) 
        #filter dataset by end date
        final_df =  final_df[final_df['date'] <= self.end]
        
        self.final_df = final_df
        return self.final_df
         
    def save_to_csv(self):
        """
        save dataframes to csv files
        """
        start = self.start.replace('-','')
        end = self.end.replace('-','')
        
        path_dir = 'data/{}'.format(datetime.strftime(datetime.today(), '%Y%m%d'))
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        path = os.path.join(path_dir, '{item}_{code}_{start}_{end}.csv'.format(item = self.item_name,code=self.code, 
                                                                               start=start, end=end))
        self.filename = '{item}_{code}_{start}_{end}'.format(item = self.item_name,code=self.code, 
                                                         start=start, end=end)
        files_present = glob.glob(path)
        if not files_present:
            self.final_df.to_csv(path, index=False)
            print('Succesfully Saved in {}'.format(path))
        else:
            print("WARNING: This file already exists!")
        return self.filename
            
    def save_to_mysql(self):
        """
        save dataframes to mysql server
        """
        engine = create_engine("mysql+pymysql://root:"+"root"+"@localhost:3306/stock_price?charset=utf8", encoding='utf-8')
        conn = engine.connect()
        print('Succesfully Saved in MySQL Server')
        self.final_df.to_sql(name=self.filename.lower(), con=engine, if_exists='replace', index=False)
        conn.close()


# In[6]:


if __name__== "__main__":
    item_list = ['SK','신풍제약'] 
    for item_name in item_list:
        print('Item Name:',item_name)
        MyStock = get_stock_price(item_name=item_name)
        MyStock.get_date()
        MyStock.get_company_code()   
        MyStock.get_last_page()
        MyStock.get_final_df()
        MyStock.save_to_csv()
        MyStock.save_to_mysql()
        print()


# In[ ]:




