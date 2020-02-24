#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime
import numpy as np
from pandas_datareader import data as pdr
import bs4 as bs
import os 
import pandas as pd
import glob

from plotly.offline import plot
import plotly.graph_objs as go


class Data:

    def __init__(self):

        self.base = 'https://finance.yahoo.com/'
        self.endpoints = {
            "klines": '/api/v3/klines',
            "cryptocurrencies": '/cryptocurrencies',
        }
        self.startdate = datetime(2000, 1, 1)
        self.enddate = datetime.today()
        self.path = os.getcwd() + '/'
        self.rsi_period = 14

    def getSymbols(self):

        url = self.base + self.endpoints["cryptocurrencies"]

        resp = requests.get(url)
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table', {'class': 'W(100%)'})  # find table in this page
        tickers = []  # save tickers column here

        for row in table.findAll('tr')[1:]:  # each row is identified by header('tr') in html code
            ticker = row.findAll('td')[0].text  # find the first cell and extract from the text
            tickers.append(ticker)

        return tickers
    
    def getData(self, tickers):
        
        return pdr.get_data_yahoo(tickers, self.startdate, self.enddate).reset_index().drop(columns= {'Adj Close'})
    
    def computeIndicators(self, df):
    
        #get moving average
        df['20_sma'] = df['Close'].rolling(20).mean()
        df['50_sma'] = df['Close'].rolling(50).mean()
        df['200_sma'] = df['Close'].rolling(200).mean()

        #get bollinger bands
        ##########   CHANGE 0.5  ############
        df['low_boll'] =  df['50_sma'] - 0.5 * np.std(df['200_sma'])
        df['high_boll'] = df['50_sma'] + 0.5 * np.std(df['200_sma'])
        
        #get returns
        df['daily_returns'] = df['Close'].pct_change(1)
        df['monthly_returns'] = df['Close'].pct_change(31)
        df['annual_returns'] = df['Close'].pct_change(365)
    
        #Compute RSI
        delta = df['Close'].diff().dropna()
        delta = delta.diff().dropna()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        roll_up = up.rolling(self.rsi_period).mean()
        roll_down = down.abs().rolling(self.rsi_period).mean()
        rs = roll_up / roll_down
        df['rsi'] = 100.0 - (100.0 / (1.0 + rs))
        
        return df
    
    def stratMA(self, df):
        
        df['signal_ma'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['20_sma'].iloc[i] > df['50_sma'].iloc[i]):
                buy_auto = False
                df['signal_ma'].iloc[i] = "buy"
               
            if (buy_auto == False) & (df['20_sma'].iloc[i] < df['50_sma'].iloc[i]):
                buy_auto = True
                df['signal_ma'].iloc[i] = "sell"
                
        return df
    
    def stratBO(self, df):
        
        df['signal_bo'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['low_boll'].iloc[i] > df['Close'].iloc[i]):
                buy_auto = False
                df['signal_bo'].iloc[i] = "buy"
               
            if (buy_auto == False) & ((df['high_boll'].iloc[i] < df['Close'].iloc[i])):
                buy_auto = True
                df['signal_bo'].iloc[i] = "sell"
                
        return df
    
    def stratRSI(self, df):
        
        df['signal_rsi'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['rsi'].iloc[i] < 40):
                buy_auto = False
                df['signal_rsi'].iloc[i] = "buy"
               
            if (buy_auto == False) & (df['rsi'].iloc[i] > 60):
                buy_auto = True
                df['signal_rsi'].iloc[i] = "sell"
                
        return df
    
    def computeStrategies(self, df):
        
        df = self.stratBO(df)
        df = self.stratMA(df)
        df = self.stratRSI(df)
        
        return df
    
    def exportData(self, df, ticker):
        df.to_csv(self.path + ticker + '.csv')
    
    #Move this function
    def plotData(self, df):

        # plot candlestick chart
        candle = go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            close=df['Close'],
            high=df['High'],
            low=df['Low'],
            name="Candlesticks")

        # plot MAs
        ssma = go.Scatter(
            x=df['Date'],
            y=df['20_sma'],
            name="20 SMA",
            line=dict(color=('rgba(102, 207, 255, 50)')))

        msma = go.Scatter(
            x=df['Date'],
            y=df['50_sma'],
            name="50 SMA",
            line=dict(color=('rgba(255, 207, 102, 50)')))

        fsma = go.Scatter(
            x=df['Date'],
            y=df['200_sma'],
            name="200 SMA",
            line=dict(color=('rgba(207, 255, 102, 50)')))

        lowbb = go.Scatter(
            x=df['Date'],
            y=df['low_boll'],
            name="Lower Bollinger Band",
            line=dict(color=('rgba(50, 102, 255, 50)')))

        highbb = go.Scatter(
            x=df['Date'],
            y=df['high_boll'],
            name="High Bollinger Band",
            line=dict(color=('rgba(50, 102, 255, 50)')))

        data = [candle, ssma, msma, fsma, lowbb, highbb]
        
        layout = go.Layout()
        fig = go.Figure(data=data, layout=layout)
        plot(fig)

class Analysis:
    
    def __init__(self):
        
        self.path = os.getcwd() + '/'
        self.extension = 'csv'
        self.files = self.getFiles()
        
    def getFiles(self):
        return glob.glob('*.{}'.format(self.extension))
    
    def computeStrategyReturns(self):
        
        for file in self.files:
        
            df = pd.read_csv(self.path + file)
            col  = [col for col in df.columns if 'signal' in col]
            
            for strategy in col:
   
                if 'bo' in strategy:  
                    
                    df_bo = df.loc[df[strategy].notnull()]
                    df_bo.loc[:, 'traded_value'] = np.where(df_bo[strategy] == "buy", df_bo['Low'] * -1, df_bo['High'])
                    print(strategy, df_bo["traded_value"]) #.sum()
                                      
                if 'ma' in strategy:
                    df_ma = df.loc[df[strategy].notnull()]
                    df_ma.loc[:, 'traded_value'] = np.where(df_ma[strategy] == "buy", df_ma['Low'] * -1, df_ma['High'])
                    print(strategy, df_ma["traded_value"]) #.sum()
                    
                if 'rsi' in strategy:
                    df_rsi = df.loc[df[strategy].notnull()]
                    df_rsi.loc[:, 'traded_value'] = np.where(df_rsi[strategy] == "buy", df_rsi['Low'] * -1, df_rsi['High'])
                    print(strategy, df_rsi["traded_value"]) #.sum()
        
def Main():
    
    data = Data()
    tickers = data.getSymbols()
    
    #On prend juste les 10 premiers pour le moment 
    for i in range(10):
        
        df = data.getData(tickers[i])
        df = data.computeIndicators(df)
        df = data.computeStrategies(df)

        #data.plotData(df)
        data.exportData(df, tickers[i])

    analysis_files = Analysis()
    analysis_files.computeStrategyReturns()
    
if __name__ == '__main__':
    Main()
