import pandas as pd
import numpy as np
import plotly.express as px  # (version 4.7.0)
import plotly.graph_objects as go

import dash  # (version 1.12.0) pip install dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)
app.title = 'Craft Beers'
server = app.server

# ------------------------------------------------------------------------------
# Import and clean data (importing csv into pandas)
df = pd.read_csv("data/preprocessed_data.csv", index_col=0)
df.reset_index(inplace=True)

df_map = pd.read_csv('data/map_data.csv', index_col=0)
df_map.reset_index(drop=True)

TABLE_DATA = df.drop(columns=['Ale', 'index', 'State', 'Type'])
MAP_DATA = df_map
PAGE_SIZE = 10

chore_map = px.choropleth(MAP_DATA, locations="Country ID",
                          color="Created Beer",
                          hover_name="Country",
                          color_continuous_scale='sunsetdark')
treemap = px.treemap(df,
                     path=['Ale', 'Type', 'Style'],
                     color='Alcohol By Volume',
                     hover_data=['Style'],
                     color_continuous_scale='RdBu'
                     )
# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Craft Beers", style={'text-align': 'center', 'font-size': '4em'}),

    html.Br(),

    html.Div(id='tree', children=[
        html.H1("Select your favorite beer", style={'text-align': 'center', 'vertical-align': 'bottom'}),
        dcc.Graph(id='tree_map', figure=treemap),
    ]),


    html.Div(id='output_container2', style={'display': 'flex'}, children=[
        html.Div(id='output_container_map', style={'width': '50%'}, children=[
            html.H1("Origin of the beers", style={'text-align': 'center'}),
            dcc.Graph(id='chore_map', figure=chore_map)]),
        html.Div(id='output_container_table', style={'width': '50%'}, children=[
            html.H1("Beers detail", style={'text-align': 'center'}),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in TABLE_DATA.columns],
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                sort_action='custom',
                sort_mode='single',
                sort_by=[],
                style_cell={'textAlign': 'center'}
            )]),
    ]),
])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [
        Output(component_id='chore_map', component_property='figure'),
        Output(component_id='table', component_property='data'),
    ],
    [
        Input(component_id='tree_map', component_property='clickData'),
        Input(component_id='table', component_property="page_current"),
        Input(component_id='table', component_property="page_size"),
        Input(component_id='table', component_property='sort_by')
    ]
)
def write_graph(click_data, page_current, page_size, sort_by):
    table_data = df
    maps = chore_map
    map_data = MAP_DATA

    if click_data:
        label = click_data['points'][0]['id'].split('/') if 'id' in click_data['points'][0].keys() else []

        # Compare if LAST_LABEL is not the same as actual label
        # if "/".join(label) == "/".join(last_label):
        #     # print("\tVykonavam pop", len(label), "/".join(label), "/".join(last_label))
        #     label.pop() if len(label) > 3 else label
        #     label.pop() if len(label) != 0 else label

        if len(label) < 1:
            table_data = df
        elif len(label) >= 3:
            style = "/".join(label[2:])
            table_data = df[df['Style'] == style]
        elif len(label) == 2:
            table_data = df[df['Type'] == label[1]]
        elif len(label) == 1:
            table_data = df[df['Ale'] == label[0]]

        table_data = table_data.drop(columns=['Ale', 'index', 'State', 'Type'])

        origin_country = table_data.groupby('Country').size()
        origin_country["United States"] = origin_country["United States"] * 0.10

        map_data['Created Beer'] = map_data['Country'].apply(
            lambda x: origin_country[x] if x in origin_country.index else 0)
        map_data = map_data.loc[map_data['Created Beer'] != 0]

        maps = px.choropleth(map_data, locations="Country ID",
                             color="Created Beer",
                             hover_name="Country",
                             color_continuous_scale='sunsetdark')

    if len(sort_by):
        table_data = table_data.sort_values(
            sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
        )
    else:
        table_data = table_data

    return maps, table_data.iloc[
                 page_current * page_size:(page_current + 1) * page_size
                 ].to_dict('records')


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
