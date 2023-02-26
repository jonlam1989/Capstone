import numpy as np
import pandas as pd

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# 1. Used to check the existing account details of a customer.
# 2. Used to modify the existing account details of a customer.
# 3. Used to display the transactions made by a customer between two dates. 
#    (Order by year, month, and day in descending order.)
#----------------------------------------------------------------------------------------------------------
# read cleaned data
customer_df = pd.read_csv('cleaned_files/cleaned_customer.csv')
credit_card_df = pd.read_csv('cleaned_files/cleaned_credit.csv')
credit_card_df.rename(columns={'CUST_CC_NO': 'CREDIT_CARD_NO'}, inplace=True)
credit_card_df['TIMEID'] = pd.to_datetime(credit_card_df['TIMEID'], format='%Y%m%d')

# date range
min_date = credit_card_df['TIMEID'].min()
max_date = credit_card_df['TIMEID'].max()

# remove CUST_ from each column - to reduce datatable size
for column in customer_df.columns:
    customer_df.rename(columns={column: column.replace('CUST_', '')}, inplace=True)
#----------------------------------------------------------------------------------------------------------
# Plotly Dash App
app = Dash(__name__)
# for multi-page functionality
dash.register_page(__name__)

layout = html.Main([
    html.Div([
        html.H2('Customer Details', id='details_header'),
        html.Label('Search customer details by full name: '),
        html.Br(),
        dcc.Input(id='first', type='text', placeholder='First Name', debounce=True),                # debounce = delay
        dcc.Input(id='middle', type='text', placeholder='Middle Name', debounce=True),
        dcc.Input(id='last', type='text', placeholder='Last Name', debounce=True),
        html.A(html.Button('Clear all fields'), href='/pages/customers-details'),
        html.Div(id='error'),
        dash_table.DataTable(id='details',
                            style_as_list_view=True,
                            style_header={'fontWeight': 'bold'},
                            style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'}),
        html.H2('Customer Transactions', id='transactions_header'),
        html.Div([
            dcc.DatePickerRange(id='date_range', 
                                min_date_allowed=min_date, 
                                max_date_allowed=max_date,
                                end_date=max_date)
        ], className='date_container'),
        dash_table.DataTable(id='transaction', 
                            page_size=10,
                            style_as_list_view=True,
                            style_header={'fontWeight': 'bold'},
                            style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'})
    ], className='main_container')
], className='details')
#----------------------------------------------------------------------------------------------------------
# update customer details based on user input - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    [Output('error', 'children'), Output('details', 'data'), Output('transaction', 'data')],
    [Input('first', 'value'), Input('middle', 'value'), Input('last', 'value'), 
     Input('date_range', 'start_date'), Input('date_range', 'end_date')]
)
def update_details(first, middle, last, start_date, end_date):
    if first and middle and last:
        # change everything to lowercase for case-insensitivity
        first_name = customer_df['FIRST_NAME'].str.lower() == first.lower()
        middle_name = customer_df['MIDDLE_NAME'].str.lower() == middle.lower()
        last_name = customer_df['LAST_NAME'].str.lower() == last.lower()

        # find customer based on full name in customer_df
        target_customer_df = customer_df[first_name & middle_name & last_name]
        
        # print error message if dataframe is empty=(name is NOT found)
        if target_customer_df.empty:
            return ['No customer found with this name...please try again', None, None]
        else:
            # find customer based on ssn in credit_card_df
            ssn = target_customer_df['SSN'].values[0]
            customer = credit_card_df['CUST_SSN'] == ssn
            target_transactions_df = credit_card_df[customer]

            # drop SSN for customer privacy
            target_transactions_df = target_transactions_df.drop(columns=['CUST_SSN'])
            target_customer_df = target_customer_df.drop(columns=['SSN', 'LAST_UPDATED'])

            # filter for date range
            if start_date and end_date:
                start = target_transactions_df['TIMEID'] >= start_date
                end = target_transactions_df['TIMEID'] <= end_date

                target_transactions_df = target_transactions_df[start & end]
                target_transactions_df = target_transactions_df.sort_values('TIMEID', ascending=False)

            target_transactions_df['TIMEID'] = credit_card_df['TIMEID'].dt.date
            # return customer details + customer transactions if name is found
            return ['', target_customer_df.to_dict('records'), target_transactions_df.to_dict('records')]
    else:
        # defaults - when the page first loads 
        return ['', None, None]
