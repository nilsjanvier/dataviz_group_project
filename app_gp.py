import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime as dt
from plotly.subplots import make_subplots


import pandas as pd

from code2 import main as core_analysis

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')



tickers, liste_df, liste_returns, figure = core_analysis()

available_indicators = df['Indicator Name'].unique()


# Returns Top cell bar for header area
def get_top_bar_cell(cellTitle, cellValue):
    return html.Div(
        className="two-col",
        children=[
            html.P(className="p-top-bar", children=cellTitle),
            html.P(id=cellTitle, className="display-none", children=cellValue),
            html.P(children=(cellValue)),
        ],
    )


# Returns HTML Top Bar for app layout
def get_top_bar(
    sharpe=3.432, returns=6577, volatility=32.112, time_day = str(dt.today())[:16]
):
    return [
        #get_top_bar_cell("Sharpe", sharpe),
        #get_top_bar_cell("Return", returns),
        #get_top_bar_cell("Volatility", volatility),
        get_top_bar_cell("Last Date", time_day)
    ]

assets = ['BTC','ETH','XRP']
strategies = ['moving average', 'boolinger bands', 'RSI', 'other']



# returns chart div
def chart_div(pair):
    return html.Div(
        id=pair + "graph_div",
        className="display-none",
        children=[
            html.Div(
                id=pair + "menu",
                className="not_visible",
                children=[
                    # Styles checklist
                    html.Div(
                        id=pair + "style_tab",
                        children=[
                            dcc.RadioItems(
                                id=pair + "chart_type",
                                options=[
                                    {
                                        "label": "Candlesticks",
                                        "value": "candlestick_trace",
                                    }
                                ],
                                value="colored_bar_trace",
                            )
                        ],
                    )         
                ]
            ),
            # Graph div
            html.Div(
                dcc.Graph(
                    id=pair + "chart",
                    className="chart-graph",
                    config={"displayModeBar": False, "scrollZoom": True},
                )
            ),
        ]
    )



app.layout = html.Div([
    html.Div(
        className="three columns div-left-panel",
        children=[
            html.Div(
                className="div-info",
                children=[
                    html.Img(
                        className="logo", src=app.get_asset_url("NEOMA_LOGOTYPE_RVB_F_V.png")
                    ),
                    html.H6(children="Trading Strategies Exploration"),
                    html.P([
                        """
                        This app introduces the results of 3 trading strategies for the 50 main cryptocurrencies quoted on Yahoo Finance. 
                        You can select the cryptocurrency that you want to show with the button on the left,
                        and the price in USD will be shown on the first graph while the bar chart will 
                        introduce the profit for each strategy.
                        """, html.Br(),"""
                        """, html.Br(),"""
                        The first strategy is based on a momentum indicator: RSI.
                        The second one is based on a trend indicator: moving averages.
                        The last one is based on a volatility indicator: bollinger bands. 
                        """, html.Br(),"""
                        Every profit is given in USD.
                        """, html.Br(),"""
                        """, html.Br(),"""
                        Data frequency is daily.
                        This frequency is not suitable for RSI and bollinger band strategies.
                        The parameters must be adjusted to increase the number of trades and thus increase the returns.
                        """, html.Br(),"""
                        Past performance does not prejudge future performance.
                        """
                        ]),
                    html.P(["""
                        ---------------------------------------
                        """, html.Br(),"""
                        This work has been done by:
                        """, html.Br(),"""
                        - Julien Romano
                        """, html.Br(),"""
                        - Marc Jeulin
                        """, html.Br(),"""
                        - Nils Janvier
                        """
                           ]),
                     ],
                 )
        ]),
    html.Div(
        className="nine columns div-right-panel",
        children=[
#             html.Div(
#                 id="top_bar", className="row div-top-bar", children=get_top_bar()
#             ),
#             html.Div([
#                 dcc.Dropdown(
#                     id = "asset",
#                     options = [{'label' : i, 'value' : i} for i in tickers],
#                     value = 'BTC_USD'
#                 )
#             ],
#             style = {'width' : '16%', 'display' : 'inline-block'}
#             ),
#             html.Div([
#                 dcc.Dropdown(
#                     id = "strategies",
#                     options = [{'label' : i, 'value' : i} for i in strategies],
#                     value = 'moving average'
#                 )
#             ],
#             style = {'width' : '20%', 'display' : 'inline-block'}
#             ),
            html.Div(
                    id="charts",
                    className="row",
                    children= [
                        html.Div(
                            dcc.Graph(
                                id='pair' + "chart",
                                figure = {
                                    "data" : figure.data,
                                    "layout" : figure.layout}
                            )
                        )
                    ]
            ),
            html.Div(
                        id='update_date',
                        className='row div-top-bar',
                        children=get_top_bar()
                        ),
        ]
    ),
    html.Div(id="orders", style={"display": "none"}),

])



if __name__ == '__main__':
    app.run_server(debug=True)