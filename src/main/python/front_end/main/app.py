#!/usr/bin/python3
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
from datetime import date, timedelta, datetime
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import colorsys
from flask import Flask
import data_access_layer as dal


# Here"s my cool App
server = Flask(__name__)
app = dash.Dash(__name__, server = server)

# Constants
colors = {
    "blue": "#4285f4",
    "white": "#fff2ff"
}

LANGUAGES = [
    "C#",
    "Haskell",
    "Java",
    "JavaScript",
    "Kotlin",
    "Python",
    "Rust",
    "Scala"
]

# Define the components
language_dropdown = dcc.Dropdown(
    id = "language_dropdown",
    options = [{"label": l, "value": l} for l in LANGUAGES],
    placeholder = "Select a language"
)

package_dropdown = dcc.Dropdown(
    id = "package_dropdown",
    options = [],
    multi = True,
    placeholder="Select an import",
)

end_date = date.today() - timedelta(1)
eval_date = dcc.DatePickerRange(
    id = 'eval_date',
    start_date = end_date - timedelta(weeks = 2),
    end_date = end_date
)

app.layout = html.Div(
    style = {"backgroundColor": colors["blue"], "color": colors["white"]},
    className = 'ten columns offset-by-one',
    children = [
        html.Div(
            style = {'margin-left': '60', 'margin-right': '60', 'margin-bottom': '60', 'margin-top': '30'},
            children = [
                html.H1("GitHub Import Analytics", style={"textAlign": "center"}),
                # subtitle,
                html.Div(style = {'color': colors['blue']},
                className = 'row',
                children = [
                html.Div([
                        html.H5("Language", style = {'color': colors['white']}),
                        language_dropdown
                        ],
                    className='four columns',
                    style={'margin-top': '10'}
                    ),
                html.Div([
                        html.H5("Import", style = {'color': colors['white']}),
                        package_dropdown
                        ],
                    className='four columns',
                    style={'margin-top': '10'}
                    ),
                html.Div([html.H5("Evaluation Date", style = {'color': colors['white']}),
                        eval_date
                        ],
                    className='four columns',
                    style={'margin-top': '10'}
                    ),
                ]),
                html.Div([
                    html.Div([
                        dcc.Graph(
                            style={'height': 250},
                            id='imports_by_date_graph'
                            )],
                        className='twelve columns',
                        style={'margin-top': '10'}
                        )], # style = {"backgroundColor": colors["blue"], 'color': colors['white']},
                className='row',
                ),
                html.Div([
                    html.Div([dcc.Graph(id = 'import_summary_bar', style = {'height': 400})],
                        className='six columns',
                        style={'margin-top': '10'}
                        ),
                    html.Div([dcc.Graph(id = 'language_share_pie', style = {'height': 400})],
                            className='six columns',
                            style={'margin-top': '10'}
                        )
                    ],
                    className='row'
                ),
        ])
])
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

@app.callback(
    Output("language_share_pie", "figure"),
    [Input("eval_date", "end_date")])
def refresh_language_share_pie(date):
    language_totals = dal.get_language_totals(date)
    data = dict(
            type='pie',
            labels=language_totals['language_name'],
            values=language_totals['total_daily_usage'],
            name='Well Type Breakdown',
            # hoverinfo="label+text+value+percent",
            # textinfo="label+percent+name",
            hole=0.5
            # marker=dict(),
            # domain={"x": [0.55, 1], 'y':[0.2, 0.8]},
            )
    figure = dict(data = data)
    return figure

@app.callback(
    Output("package_dropdown", "options"),
    [Input("language_dropdown", "value")])
def language_dropdown(language):
    unique_packages = dal.get_packages_by_language(language)
    return [{"label": l, "value": l} for l in unique_packages.import_name]

@app.callback(
    Output("import_summary_bar", "figure"),
    [Input("language_dropdown", "value"), Input("eval_date", "end_date")])
def refresh_import_summary_bar(language, end_date):
    package_data = dal.get_most_used_languages(language, end_date)
    return go.Figure(
            data = [go.Bar(
                x = package_data['usage_count'][::-1],
                y = package_data['import_name'][::-1],
                name = 'Imports',
                orientation = 'h'
                # marker = go.Marker(color = rgb)
                )],
            layout = go.Layout(
                title = 'Daily Import Summary',
            )
        )


@app.callback(
    Output("imports_by_date_graph", "figure"),
    [Input("language_dropdown", "value"), Input("package_dropdown", "value"),
    Input("eval_date", "start_date"), Input("eval_date", "end_date")])
def refresh_imports_by_date_graph(language, packages, start_date, end_date):
    if packages == None:
        return None

    package_data = dal.get_usage_by_import(language, packages, start_date, end_date)
    colors = gen_colors(len(packages))

    def make_trace(df, package, rgb):
        x_date = df['commit_date']
        y_package = df[package]
        return go.Trace(
            x = x_date,
            y = y_package,
            name = package,
            marker = go.Marker(color = rgb)
            )
    return go.Figure(
            data=[make_trace(package_data, package, colors[i]) for i, package in enumerate(packages)],
            layout = go.Layout(
                title='Imports over Time',
                showlegend = True,
                legend = go.Legend(x = 0, y = 1.0),
                margin = go.Margin(l = 40, r = 40, t = 40, b = 30)
                )
            )

def gen_colors(n):
    HSV_tuples = [(x*1.0/n, 0.5, 0.5) for x in range(n)]
    return list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))

if __name__ == "__main__":
    app.run_server(debug = True, host="0.0.0.0")
