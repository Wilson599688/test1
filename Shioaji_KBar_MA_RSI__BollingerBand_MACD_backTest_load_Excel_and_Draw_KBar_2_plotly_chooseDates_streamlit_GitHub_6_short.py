# 載入必要模組
import os
# os.chdir(r'C:\Users\user\Dropbox\系務\專題實作\112\金融看板\for students')
#import haohaninfo
#from order_Lo8 import Record
import numpy as np
import talib as ta
#from talib.abstract import SMA,EMA, WMA, RSI, BBANDS, MACD
#import sys
# import indicator_f_Lo2_short,datetime, indicator_forKBar_short
import datetime
import pandas as pd
import streamlit as st 
import streamlit.components.v1 as stc 


###### (1) 開始設定 ######
html_temp = """
        <div style="background-color:#3872fb;padding:10px;border-radius:10px">
        <h1 style="color:white;text-align:center;">金融資料視覺化呈現 (金融看板) </h1>
        <h2 style="color:white;text-align:center;">Financial Dashboard </h2>
        </div>
        """
stc.html(html_temp)

## 读取Pickle文件
df_original = pd.read_pickle('kbars_2330_2022-01-01-2022-11-18.pkl')


df_original = df_original.drop('Unnamed: 0',axis=1)

##### 選擇資料區間
st.subheader("選擇開始與結束的日期, 區間:2022-01-03 至 2022-11-18")
start_date = st.text_input('選擇開始日期 (日期格式: 2022-01-03)', '2022-01-03')
end_date = st.text_input('選擇結束日期 (日期格式: 2022-11-18)', '2022-11-18')
start_date = datetime.datetime.strptime(start_date,'%Y-%m-%d')
end_date = datetime.datetime.strptime(end_date,'%Y-%m-%d')
# 使用条件筛选选择时间区间的数据
df = df_original[(df_original['time'] >= start_date) & (df_original['time'] <= end_date)]


###### (2) 轉化為字典 ######:
KBar_dic = df.to_dict()

KBar_open_list = list(KBar_dic['open'].values())
KBar_dic['open']=np.array(KBar_open_list)

KBar_dic['product'] = np.repeat('tsmc', KBar_dic['open'].size)

KBar_time_list = list(KBar_dic['time'].values())
KBar_time_list = [i.to_pydatetime() for i in KBar_time_list] ## Timestamp to datetime
KBar_dic['time']=np.array(KBar_time_list)

KBar_low_list = list(KBar_dic['low'].values())
KBar_dic['low']=np.array(KBar_low_list)

KBar_high_list = list(KBar_dic['high'].values())
KBar_dic['high']=np.array(KBar_high_list)

KBar_close_list = list(KBar_dic['close'].values())
KBar_dic['close']=np.array(KBar_close_list)

KBar_volume_list = list(KBar_dic['volume'].values())
KBar_dic['volume']=np.array(KBar_volume_list)

KBar_amount_list = list(KBar_dic['amount'].values())
KBar_dic['amount']=np.array(KBar_amount_list)

######  (3) 改變 KBar 時間長度 (以下)  ########

Date = start_date.strftime("%Y-%m-%d")

st.subheader("設定一根 K 棒的時間長度(分鐘)")
cycle_duration = st.number_input('輸入一根 K 棒的時間長度(單位:分鐘, 一日=1440分鐘)', key="KBar_duration")
cycle_duration = int(cycle_duration)

KBar = indicator_forKBar_short.KBar(Date,cycle_duration)    ## 設定cycle_duration可以改成你想要的 KBar 週期

for i in range(KBar_dic['time'].size):
    
    time = KBar_dic['time'][i]
    open_price= KBar_dic['open'][i]
    close_price= KBar_dic['close'][i]
    low_price= KBar_dic['low'][i]
    high_price= KBar_dic['high'][i]
    qty =  KBar_dic['volume'][i]
    amount = KBar_dic['amount'][i]
    tag=KBar.AddPrice(time, open_price, close_price, low_price, high_price, qty)

KBar_dic = {}

## 形成 KBar 字典 (新週期的):
KBar_dic['time'] =  KBar.TAKBar['time']   
KBar_dic['product'] = np.repeat('tsmc', KBar_dic['time'].size)
KBar_dic['open'] = KBar.TAKBar['open']
KBar_dic['high'] =  KBar.TAKBar['high']
KBar_dic['low'] =  KBar.TAKBar['low']
KBar_dic['close'] =  KBar.TAKBar['close']
KBar_dic['volume'] =  KBar.TAKBar['volume']

######  改變 KBar 時間長度 (以上)  ########


###### (4) 計算各種技術指標 ######
##### 將K線 Dictionary 轉換成 Dataframe
KBar_df = pd.DataFrame(KBar_dic)

#####  (i) 移動平均線策略   #####
####  設定長短移動平均線的 K棒 長度:
st.subheader("設定計算長移動平均線(MA)的 K 棒數目(整數, 例如 10)")
LongMAPeriod=st.slider('選擇一個整數', 0, 100, 10)
st.subheader("設定計算短移動平均線(MA)的 K 棒數目(整數, 例如 2)")
ShortMAPeriod=st.slider('選擇一個整數', 0, 100, 2)

#### 計算長短移動平均線
KBar_df['MA_long'] = KBar_df['close'].rolling(window=LongMAPeriod).mean()
KBar_df['MA_short'] = KBar_df['close'].rolling(window=ShortMAPeriod).mean()

#### 尋找最後 NAN值的位置
last_nan_index_MA = KBar_df['MA_long'][::-1].index[KBar_df['MA_long'][::-1].apply(pd.isna)][0]


#####  (ii) RSI 策略   #####
#### 順勢策略
### 設定長短 RSI 的 K棒 長度:
st.subheader("設定計算長RSI的 K 棒數目(整數, 例如 10)")
LongRSIPeriod=st.slider('選擇一個整數', 0, 1000, 10)
st.subheader("設定計算短RSI的 K 棒數目(整數, 例如 2)")
ShortRSIPeriod=st.slider('選擇一個整數', 0, 1000, 2)

### 計算 RSI指標長短線, 以及定義中線
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

KBar_df['RSI_long'] = calculate_rsi(KBar_df, LongRSIPeriod)
KBar_df['RSI_short'] = calculate_rsi(KBar_df, ShortRSIPeriod)
KBar_df['RSI_Middle']=np.array([50]*len(KBar_dic['time']))

### 尋找最後 NAN值的位置
last_nan_index_RSI = KBar_df['RSI_long'][::-1].index[KBar_df['RSI_long'][::-1].apply(pd.isna)][0]

###### 新增 KDJ 指标 ######
st.subheader("設定 KDJ 指标的參數")
KDJ_n = st.slider('選擇 KDJ 的 K參數', 1, 100, 9)
KDJ_m1 = st.slider('選擇 KDJ 的 D參數', 1, 100, 3)
KDJ_m2 = st.slider('選擇 KDJ 的 J參數', 1, 100, 3)

low_list = KBar_df['Low'].rolling(window=KDJ_n, min_periods=1).min()
high_list = KBar_df['High'].rolling(window=KDJ_n, min_periods=1).max()
rsv = (KBar_df['Close'] - low_list) / (high_list - low_list) * 100

KBar_df['K'] = rsv.ewm(com=(KDJ_m1-1)).mean()
KBar_df['D'] = KBar_df['K'].ewm(com=(KDJ_m2-1)).mean()
KBar_df['J'] = 3 * KBar_df['K'] - 2 * KBar_df['D']

### 尋找最後 NAN值的位置
last_nan_index_KDJ = KBar_df['K'][::-1].index[KBar_df['K'][::-1].apply(pd.isna)][0]


###### 新增 SAR 指标 ######
st.subheader("設定 SAR 指标的參數")
SAR_acceleration = st.slider('選擇 SAR 的加速因子', 0.01, 0.1, 0.02)
SAR_maximum = st.slider('選擇 SAR 的最大加速因子', 0.1, 0.5, 0.2)

KBar_df['SAR'] = ta.SAR(KBar_df['High'], KBar_df['Low'], acceleration=SAR_acceleration, maximum=SAR_maximum)

### 尋找最後 NAN值的位置
last_nan_index_SAR = KBar_df['SAR'][::-1].index[KBar_df['SAR'][::-1].apply(pd.isna)][0]


###### 新增 ATR 指标 ######
st.subheader("設定 ATR 指标的參數")
ATR_period = st.slider('選擇 ATR 的周期', 1, 50, 14)

KBar_df['ATR'] = ta.ATR(KBar_df['High'], KBar_df['Low'], KBar_df['Close'], timeperiod=ATR_period)

### 尋找最後 NAN值的位置
last_nan_index_ATR = KBar_df['ATR'][::-1].index[KBar_df['ATR'][::-1].apply(pd.isna)][0]


##### 繪圖
st.line_chart(KBar_df[['time','close', 'MA_long','MA_short']][last_nan_index_MA:])
st.line_chart(KBar_df[['time','RSI_long','RSI_short','RSI_Middle']][last_nan_index_RSI:])
st.line_chart(KBar_df[['time','K','D','J']][last_nan_index_KDJ:])
st.line_chart(KBar_df[['time','SAR']][last_nan_index_SAR:])
st.line_chart(KBar_df[['time','ATR']][last_nan_index_ATR:])

###### 顯示更新資料表格
st.write(KBar_df)
