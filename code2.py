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
import plotly.io as pio
pio.templates

from plotly.subplots import make_subplots

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
    def defineFig(self, df, returns, plotTicker, size):
        
        layout = go.Layout()
        fig = go.Figure(layout=layout)
        
        fig = make_subplots(
            rows=2, cols=1,
            column_widths=[0.6],
            row_heights=[1, 0.3],
            subplot_titles=("Prices", "Profit per strategy"),
            vertical_spacing = 0.3,
            specs=[[{"type": "scatter"}],
                   [{"type": "bar"}]])
        fig.add_trace(
            go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            close=df['Close'],
            high=df['High'],
            low=df['Low'],
            name="Candlesticks"),
            row=1, col=1)
        fig.add_trace(
            go.Scatter(
            x=df['Date'],
            y=df['20_sma'],
            name="20 SMA",
            line=dict(color=('rgba(102, 207, 255, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['50_sma'],
            name="50 SMA",
            line=dict(color=('rgba(255, 207, 102, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['200_sma'],
            name="200 SMA",
            line=dict(color=('rgba(207, 255, 102, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['low_boll'],
            name="Lower Bollinger Band",
            line=dict(color=('rgba(50, 102, 255, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['high_boll'],
            name="High Bollinger Band",
            line=dict(color=('rgba(50, 102, 255, 50)'))),
            row=1, col=1)
        x=returns.crypto
        color=np.array(['rgb(255,255,255)']*x.shape[0])
        color[x<0]='rgb(255,0, 0)'
        color[x>0]='rgb(0, 255, 0)'
        fig.add_trace(go.Bar(
            y=returns.index,
            x=x,
            orientation='h',
            marker = dict(color=color.tolist()),
            showlegend=False,
            name= "Profit per strategy"), 
            row=2, col=1)
        
        visible = [True] * 7 + [False] * 7 * (size-1)
        buttons = list()
        buttons.append(dict(label=plotTicker,
                            method="update",
                            args=[{"visible": visible},
                                   {"title": plotTicker}]))
        return fig, buttons
        
    def addNew(self, df, returns, plotTicker, prevFig, size, index, buttons):
        fig = prevFig
        fig.add_trace(
            go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            close=df['Close'],
            high=df['High'],
            low=df['Low'],
            name="Candlesticks",
            visible = False),
            row=1, col=1)
        fig.add_trace(
            go.Scatter(
            x=df['Date'],
            y=df['20_sma'],
            name="20 SMA",
            visible = False,
            line=dict(color=('rgba(102, 207, 255, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['50_sma'],
            name="50 SMA",
            visible = False,
            line=dict(color=('rgba(255, 207, 102, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['200_sma'],
            name="200 SMA",
            visible = False,
            line=dict(color=('rgba(207, 255, 102, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['low_boll'],
            name="Lower Bollinger Band",
            visible = False,
            line=dict(color=('rgba(50, 102, 255, 50)'))),
            row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['high_boll'],
            name="High Bollinger Band",
            visible = False,
            line=dict(color=('rgba(50, 102, 255, 50)'))),
            row=1, col=1)
        x=returns.crypto
        color=np.array(['rgb(255,255,255)']*x.shape[0])
        color[x<0]='rgb(255,0, 0)'
        color[x>=0]='rgb(0, 255, 0)'
        fig.add_trace(go.Bar(
            y=returns.index,
            x=x,
            orientation='h',
            showlegend=False,
            marker = dict(color=color.tolist()),
            name= "Profit per strategy",
            visible=False),
            row=2, col=1)
        fig.update_layout(template = "plotly_dark",
                          autosize=False,
                          width=1000,
                          height=1000,)
        
        visible = [False] * (7*index) + [True]*7 + [False]*(7*(size-index-1))
        buttons.append(
            dict(
                label=plotTicker,
                method="update",
                args=[{"visible": visible}, {"title": plotTicker}])
            )
        
        
        
        return fig, buttons
    
    def run(tickers, size):
        return tickers
    
    def get_returns(self, df, tickers):
        col  = [col for col in df.columns if 'signal' in col]
        strat_totals = []
        for strategy in col:
            df_temp = 0
            df_temp = df.loc[df[strategy].notnull()]
            df_temp.loc[:, 'traded_value'] = np.where(df_temp[strategy] == "buy", df_temp['Low'] * -1, df_temp['High'])
            add = df_temp.iloc[-1, df.columns.get_loc('Close')] if df_temp.iloc[-1, df.columns.get_loc(strategy)] == 'buy' else 0
            portfolio_val = df_temp["traded_value"].sum() + add
            strat_totals.append(portfolio_val)
        return pd.DataFrame(strat_totals, columns=["crypto"], index=["bollinger","moving average","rsi"])

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
                
                df_temp = df.loc[df[strategy].notnull()]
                df_temp.loc[:, 'traded_value'] = np.where(df_temp[strategy] == "buy", df_temp['Low'] * -1, df_temp['High'])
                add = df_temp.iloc[-1, df.columns.get_loc('Close')] if df_temp.iloc[-1, df.columns.get_loc(strategy)] == 'buy' else 0 
                print(f'currency : {file}, \n strategy : {strategy} : \
                      \n cash : # {df_temp["traded_value"].sum()} \
                      \n curr. position : # {add} \
                      \n total portfolio value : # {df_temp["traded_value"].sum() + add}')
                         

   
def main():
    
    data = Data()
    tickers = data.getSymbols()
    size = 50
    #On prend juste les 10 premiers pour le moment 
    df = data.getData(tickers[0])
    df = data.computeIndicators(df)
    df = data.computeStrategies(df)
    returns = data.get_returns(df, tickers[0])
    figure, buttons=data.defineFig(df, returns, tickers[0], size)
    data.exportData(df, tickers[0])
    
    liste_df = [df]
    liste_returns = [returns]
    for i in range(1, size):
        
        df = data.getData(tickers[i])
        df = data.computeIndicators(df)
        df = data.computeStrategies(df)
        figure, buttons=data.addNew(df, returns, tickers[i], figure, size, i, buttons)
        data.exportData(df, tickers[i])
        liste_df.append(df)
        returns = data.get_returns(df, tickers)
        liste_returns.append(returns)
    figure.update_layout(updatemenus=[dict(active=0, buttons=tuple(buttons))])

    analysis_files = Analysis()
    analysis_files.computeStrategyReturns()
    return tickers, liste_df , liste_returns, figure

if __name__ == '__main__':
    tickers, liste_df, df_returns, figure = main()
    # plot(figure)

