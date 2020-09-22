#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import time
from datetime import datetime
import pymysql
from real_stock_price_scraper import get_stock_price
get_ipython().run_line_magic('matplotlib', 'inline')


# In[ ]:


def save_to_mysql(self):
    """
    save dataframes to mysql server
    """
    engine = create_engine("mysql+pymysql://root:"+"root"+"@localhost:3306/stock_price?charset=utf8", encoding='utf-8')
    conn = engine.connect()
    print('Succesfully Saved in MySQL Server')

    self.final_df.to_sql(name=('{item}_{today}'.format(item=self.item_name,
                                                       today=datetime.strftime(datetime.today(), '%Y%m%d')).lower()), 
                         con=engine, if_exists='replace', index=False)
    conn.close()


# In[2]:


#mysql server credentials
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


# In[4]:


#default df(first item) for merging all data
SQL = "show tables"
pd.read_sql(SQL,db)


# In[5]:


item_list = ['삼성전자','신풍제약','SK']

#default df(first item) for merging all data
SQL = "SELECT date,close as {table} FROM {table}_{date}".format(table=item_list[0],date='20200918')
df = pd.read_sql(SQL,db)

#from second item
for item in item_list[1:]:
    SQL = "SELECT date,close as {table} FROM {table}_{date}".format(table=item, date='20200918')
    add_df = pd.read_sql(SQL,db)
    df = df.merge(add_df, on='date')    
df.columns = ['date','samsung elec','shinpung','sk']
item_list = ['samsung elec','shinpung','sk']


# In[7]:


df = df.set_index('date')


# In[8]:


df.describe().T


# In[9]:


df.dropna().plot(legend=True, figsize=(12,6))


# In[65]:


#correlation between two assets: SK and Samsung Electronics (vert weak correlation)
sns.set_style("whitegrid")
sns.jointplot(df['sk'].pct_change(),df['samsung elec'].pct_change(),kind='scatter',color='green', alpha=0.5)


# In[66]:


#correlations 
#: not strong but somewhat correlated between IT assets
pct_change_df = df.set_index('date').pct_change()
df_corr= pct_change_df.dropna().corr()

fig, ax = plt.subplots(figsize=(10,6))         
sns.heatmap(df_corr, annot=True, linewidths=.5, ax=ax)
sns.pairplot(pct_change_df.dropna())
plt.show()

