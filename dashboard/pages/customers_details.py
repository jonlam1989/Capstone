import numpy as np
import pandas as pd

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# Used to check the existing account details of a customer.
# Used to modify the existing account details of a customer.
#----------------------------------------------------------------------------------------------------------
# read cleaned data + filter for only the SSN (need this to merge dataframes) and CUST_ZIP
customer_df = pd.read_csv('cleaned_files/cleaned_customer.csv')
customer_df.drop(columns=['SSN', 'LAST_UPDATED'], inplace=True)

# remove CUST_ from each column - to reduce datatable size
for column in customer_df.columns:
    customer_df.rename(columns={column: column.replace('CUST_', '')}, inplace=True)
#----------------------------------------------------------------------------------------------------------
# Plotly Dash App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])                                   # adding BOOTSTRAP
# for multi-page functionality
dash.register_page(__name__)

layout = html.Main([
    html.Div([
        html.H2('Customer Details'),
        html.Label('Search customer details by full name: '),
        html.Br(),
        dcc.Input(id='first', type='text', placeholder='First Name', debounce=True),                # debounce = delay
        dcc.Input(id='middle', type='text', placeholder='Middle Name', debounce=True),
        dcc.Input(id='last', type='text', placeholder='Last Name', debounce=True),
        html.Div(id='error'),
        dash_table.DataTable(id='details',
                            style_as_list_view=True,
                            style_header={'fontWeight': 'bold'},
                            style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'}),
    ], className='main_container')
], className='details')
#----------------------------------------------------------------------------------------------------------
# update customer details based on user input - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    [Output('error', 'children'), Output('details', 'data')],
    [Input('first', 'value'), Input('middle', 'value'), Input('last', 'value')]
)
def update_details(first, middle, last):
    if first and middle and last:
        # data validation: change everything to lowercase for case-insensitivity
        first_name = customer_df['FIRST_NAME'].str.lower() == first.lower()
        middle_name = customer_df['MIDDLE_NAME'].str.lower() == middle.lower()
        last_name = customer_df['LAST_NAME'].str.lower() == last.lower()

        # find customer based on full name
        target_customer_df = customer_df[first_name & middle_name & last_name]
        
        # print error message if dataframe is empty=(name is NOT found)
        if target_customer_df.empty:
            return ['No customer found with this name...please try again', None]
        # return customer details if name is found
        return ['', target_customer_df.to_dict('records')]
    else:
        # defaults - when the page first loads 
        return ['', None]
