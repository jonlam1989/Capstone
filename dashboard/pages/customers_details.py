import numpy as np
import pandas as pd

import mysql.connector as mariadb
from dotenv import load_dotenv              # environment variables
import os

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# 1. Used to check the existing account details of a customer.
# 2. Used to modify the existing account details of a customer.
# 3. Used to display the transactions made by a customer between two dates. 
#    (Order by year, month, and day in descending order.)
#----------------------------------------------------------------------------------------------------------
# load the environment variables
load_dotenv()

# assign environment variables
PASSWORD = os.getenv('MariaDB_Password')
USER = os.getenv('MariaDB_Username')

# functions: get data + update data
def get_customer_data():
    try:
        # establish connection to MariaDB
        con = mariadb.connect(
            host='localhost',
            user=USER,
            password=PASSWORD,
            database='creditcard_capstone'
        )

        # create a cursor
        cur = con.cursor()
        # SQL statement
        query = ''' 
        SELECT *
        FROM cdw_sapp_customer
        '''
        # execute SQL statement
        cur.execute(query)

        # convert results to pandas dataframe
        customer_df = pd.DataFrame(cur, columns=['SSN', 
                                                 'FIRST_NAME', 
                                                 'MIDDLE_NAME', 
                                                 'LAST_NAME', 
                                                 'CREDIT_CARD_NO', 
                                                 'FULL_STREET_ADDRESS', 
                                                 'CUST_CITY', 
                                                 'CUST_STATE', 
                                                 'CUST_COUNTRY', 
                                                 'CUST_ZIP', 
                                                 'CUST_PHONE', 
                                                 'CUST_EMAIL', 
                                                 'LAST_UPDATED'])
        # close connection to MariaDB
        con.close()

        return customer_df
    except mariadb.ERROR as err:
        print(err)

def get_credit_data():
    try:
        # establish connection to MariaDB
        con = mariadb.connect(
            host='localhost',
            user=USER,
            password=PASSWORD,
            database='creditcard_capstone'
        )

        # create a cursor
        cur = con.cursor()
        # SQL statement
        query = ''' 
        SELECT *
        FROM cdw_sapp_credit_card
        '''
        # execute SQL statement
        cur.execute(query)

        # convert results to pandas dataframe
        credit_df = pd.DataFrame(cur, columns=['CUST_CC_NO', 
                                               'TIMEID', 
                                               'CUST_SSN', 
                                               'BRANCH_CODE',
                                               'TRANSACTION_TYPE', 
                                               'TRANSACTION_VALUE', 
                                               'TRANSACTION_ID'])
        # close connection to MariaDB
        con.close()

        return credit_df
    except mariadb.ERROR as err:
        print(err)

def update_customer_data(*args):
    try:
        # establish connection to MariaDB
        con = mariadb.connect(
            host='localhost',
            user=USER,
            password=PASSWORD,
            database='creditcard_capstone'
        )
        
        # create a cursor
        cur = con.cursor()
        
        # SQL statement
        query = '''
        UPDATE cdw_sapp_customer
        SET 
            FIRST_NAME = '{}', MIDDLE_NAME = '{}', LAST_NAME = '{}',
            CREDIT_CARD_NO = '{}', FULL_STREET_ADDRESS = '{}', CUST_CITY = '{}',
            CUST_STATE = '{}', CUST_COUNTRY = '{}', CUST_ZIP = '{}',
            CUST_PHONE = '{}', CUST_EMAIL = '{}'
        WHERE SSN = '{}'
        '''
        # execute SQL statement
        cur.execute(query.format(args[0], args[1], args[2], args[3], args[4], args[5], 
                                args[6], args[7], args[8], args[9], args[10], 
                                args[11]))
        con.commit()
        
        # close connection to MariaDB
        con.close()

        return cur.rowcount > 0
    except mariadb.ERROR as e:
        print(e)    
#----------------------------------------------------------------------------------------------------------
# read clean data
customer_df = get_customer_data()
credit_card_df = get_credit_data()
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
        dcc.Store(id='ssn', data=[], storage_type='memory'),                                        # store customer ssn
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
        html.Form([
            html.H2('Edit the Existing Customer Details'),
            dcc.Input(id='edit_first', type='text', value='', placeholder='Edit First Name', debounce=True), 
            dcc.Input(id='edit_mid', type='text', value='', placeholder='Edit Middle Name', debounce=True),
            dcc.Input(id='edit_last', type='text', value='', placeholder='Edit Last Name', debounce=True),
            dcc.Input(id='edit_cc', type='text', value='', placeholder='Edit Credit Card', debounce=True),
            dcc.Input(id='edit_street', type='text', value='', placeholder='Edit Street Address', debounce=True),
            dcc.Input(id='edit_city', type='text', value='', placeholder='Edit City', debounce=True),
            dcc.Input(id='edit_state', type='text', value='', placeholder='Edit State', debounce=True),
            dcc.Input(id='edit_country', type='text', value='', placeholder='Edit Country', debounce=True),
            dcc.Input(id='edit_zip', type='text', value='', placeholder='Edit Zip Code', debounce=True),
            dcc.Input(id='edit_phone', type='text', value='', placeholder='Edit Phone', debounce=True),
            dcc.Input(id='edit_email', type='text', value='', placeholder='Edit Email', debounce=True),
            html.Div(html.Button('Submit', id='Submit', n_clicks=0))
        ], id='edit_form', style={'display': 'none'}),                                              # hide the form
        html.Div(id='output'),
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
    [Output('error', 'children'), Output('details', 'data'), Output('transaction', 'data'), Output('ssn', 'data'),
     Output('edit_form', component_property='style'), Output('edit_first', 'value'), Output('edit_mid', 'value'), 
     Output('edit_last', 'value'), Output('edit_cc', 'value'), Output('edit_street', 'value'), 
     Output('edit_city', 'value'), Output('edit_state', 'value'), Output('edit_country', 'value'), 
     Output('edit_zip', 'value'), Output('edit_phone', 'value'), Output('edit_email', 'value')],
    [Input('first', 'value'), Input('middle', 'value'), Input('last', 'value'), 
     Input('date_range', 'start_date'), Input('date_range', 'end_date')]
)
def update_details(first, middle, last, start_date, end_date):
    if first and middle and last:
        # change everything to lowercase for case-insensitivity
        first_name = customer_df['FIRST_NAME'].str.lower() == first.lower().strip()
        middle_name = customer_df['MIDDLE_NAME'].str.lower() == middle.lower().strip()
        last_name = customer_df['LAST_NAME'].str.lower() == last.lower().strip()

        # find customer based on full name in customer_df
        target_customer_df = customer_df[first_name & middle_name & last_name]
        # print error message if dataframe is empty=(name is NOT found)
        if target_customer_df.empty:
            return ['(No customer found with this name...please try again)', None, None, None, {'display':'none'}, '', '', '', '', '', '', '', '', '', '', '']
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

            # return customer details + customer transactions + ssn if name is found
            # pre-populate form with current customer details
            return ['', target_customer_df.to_dict('records'), target_transactions_df.to_dict('records'), ssn,
                    {'display': 'block'},                                                           # show the form
                    target_customer_df['FIRST_NAME'].values[0], 
                    target_customer_df['MIDDLE_NAME'].values[0], 
                    target_customer_df['LAST_NAME'].values[0],
                    target_customer_df['CREDIT_CARD_NO'].values[0], 
                    target_customer_df['FULL_STREET_ADDRESS'].values[0], 
                    target_customer_df['CITY'].values[0], 
                    target_customer_df['STATE'].values[0],
                    target_customer_df['COUNTRY'].values[0], 
                    target_customer_df['ZIP'].values[0], 
                    target_customer_df['PHONE'].values[0], 
                    target_customer_df['EMAIL'].values[0] 
            ]
    else:
        # defaults - when the page first loads 
        return ['', None, None, None, {'display': 'none'}, '', '', '', '', '', '', '', '', '', '', '']
#----------------------------------------------------------------------------------------------------------
# update customer details based on user input - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    Output('output', 'children'),
    [Input('ssn', 'data'), Input('edit_first', 'value'), Input('edit_mid', 'value'), Input('edit_last', 'value'), Input('edit_cc', 'value'), 
     Input('edit_street', 'value'), Input('edit_city', 'value'), Input('edit_state', 'value'), Input('edit_country', 'value'), 
     Input('edit_zip', 'value'), Input('edit_phone', 'value'), Input('edit_email', 'value'), Input('Submit', 'n_clicks')]
)
def submit_form(ssn, edit_first, edit_mid, edit_last, edit_cc, edit_street, edit_city, 
                edit_state, edit_country, edit_zip, edit_phone, edit_email, n_clicks):
    
    if n_clicks > 0:
        # update MariaDB
        update_customer_data(edit_first, edit_mid, edit_last, edit_cc, edit_street, edit_city, 
                             edit_state, edit_country, edit_zip, edit_phone, edit_email, ssn)

        # update customer's dataframe (so don't need to restart flask server in order to view the latest changes in database)
        customer = customer_df['SSN'] == ssn

        customer_df.loc[customer, 'FIRST_NAME'] = edit_first
        customer_df.loc[customer, 'MIDDLE_NAME'] = edit_mid
        customer_df.loc[customer, 'LAST_NAME'] = edit_last
        customer_df.loc[customer, 'CREDIT_CARD_NO'] = edit_cc
        customer_df.loc[customer, 'FULL_STREET_ADDRESS'] = edit_street
        customer_df.loc[customer, 'CITY'] = edit_city
        customer_df.loc[customer, 'STATE'] = edit_state
        customer_df.loc[customer, 'COUNTRY'] = edit_country
        customer_df.loc[customer, 'ZIP'] = edit_zip
        customer_df.loc[customer, 'PHONE'] = edit_phone
        customer_df.loc[customer, 'EMAIL'] = edit_email

    return ''