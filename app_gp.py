import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime as dt
from plotly.subplots import make_subplots


import pandas as pd

import code2

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')



tickers, liste_df, figure = code2.Main()

available_indicators = df['Indicator Name'].unique()

# Display big numbers in readable format
def human_format(num):
    try:
        num = float(num)
        # If value is 0
        if num == 0:
            return 0
        # Else value is a number
        if num < 1000000:
            return num
        magnitude = int(math.log(num, 1000))
        mantissa = str(int(num / (1000 ** magnitude)))
        return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]
    except:
        return num

# Returns Top cell bar for header area
def get_top_bar_cell(cellTitle, cellValue):
    return html.Div(
        className="two-col",
        children=[
            html.P(className="p-top-bar", children=cellTitle),
            html.P(id=cellTitle, className="display-none", children=cellValue),
            html.P(children=human_format(cellValue)),
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
                    html.P(
                        """
                        This app represent different Trading 
                        strategies and their respective 
                        performances.
                        """
                        ),
                    html.P(["""
                        ---------------------------------------
                        """, html.Br(),"""
                        This work have been done by :
                        """, html.Br(),"""
                        - Julien Julius Julie
                        """, html.Br(),"""
                        - Sir Julian Van Lemen,
                        """, html.Br(),"""
                        - Marco-Julius Jeulinos \n
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
                id='update_date',
                className='row div-top-bar',
                children=get_top_bar()
            ),
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
        ]
    ),
    html.Div(id="orders", style={"display": "none"}),

])



if __name__ == '__main__':
    app.run_server(debug=True)