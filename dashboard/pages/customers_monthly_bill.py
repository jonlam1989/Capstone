import numpy as np
import pandas as pd

import mysql.connector as mariadb
from dotenv import load_dotenv              # environment variables
import os

from datetime import datetime

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# 1. Used to generate a monthly bill for a credit card number for a given month and year.
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

def get_branch_data():
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
        FROM cdw_sapp_branch
        '''
        # execute SQL statement
        cur.execute(query)

        # convert results to pandas dataframe
        branch_df = pd.DataFrame(cur, columns=['BRANCH_CODE', 
                                               'BRANCH_NAME', 
                                               'BRANCH_STREET', 
                                               'BRANCH_CITY',
                                               'BRANCH_STATE', 
                                               'BRANCH_ZIP', 
                                               'BRANCH_PHONE', 
                                               'LAST_UPDATED'])
        # close connection to MariaDB
        con.close()

        return branch_df
    except mariadb.ERROR as err:
        print(err)
#----------------------------------------------------------------------------------------------------------
# read cleaned data
branch_df = get_branch_data()
customer_df = get_customer_data()
credit_card_df = get_credit_data()
credit_card_df.rename(columns={'CUST_SSN':'SSN'}, inplace=True)

# merge both dataframes
merged_df = credit_card_df.merge(customer_df, on='SSN')
merged_df = merged_df.merge(branch_df, on='BRANCH_CODE')
merged_df.drop(columns=['SSN', 
                        'CUST_CC_NO',
                        'CUST_COUNTRY', 
                        'CUST_PHONE', 
                        'CUST_EMAIL', 
                        'BRANCH_CODE', 
                        'LAST_UPDATED_x', 
                        'LAST_UPDATED_y'], 
                        inplace=True)
merged_df['TIMEID'] = pd.to_datetime(merged_df['TIMEID'], format='%Y%m%d')
merged_df['TIMEID'] = merged_df['TIMEID'].dt.date 

# find unique months
list_of_months = pd.to_datetime(merged_df['TIMEID']).dt.month.unique()
list_of_months.sort()
months_df = pd.DataFrame(list_of_months, columns=['Filter by Month'])
# find unique years
list_of_years = pd.to_datetime(merged_df['TIMEID']).dt.year.unique()
list_of_years.sort()
years_df = pd.DataFrame(list_of_years, columns=['Filter by Year'])
#----------------------------------------------------------------------------------------------------------
# Plotly Dash App
app = Dash(__name__)
# for multi-page functionality
dash.register_page(__name__)

layout = html.Main([
    html.Div([
        html.H2('Monthly Bill Statement', id='bill_header'),
        html.Label('Generate bill by specifying credit card number, month, and year: '),
        html.Br(),
        dcc.Input(id='cc', type='text', placeholder='Credit Card Number', minLength=16, maxLength=16, debounce=True),
        html.A(html.Button('Clear all fields'), href='/pages/customers-monthly-bill'),
        html.Div(id='err'),
        html.Div([
            html.Section([
                html.Div([
                    html.Section([
                        html.Div([
                            html.H3('New Balance'),
                            html.H3(id='new_balance')
                        ], className='info'),
                        html.Div([
                            html.H3('Minimum Payment Due'),
                            html.H3(id='minimum_payment')
                        ], className='info'),
                        html.Div([
                            html.H3('Payment Due Date'),
                            html.H3(id='due_date')
                        ], className='info'),
                        html.P('Late Payment Warning: If we do not receive your minimum payment by the above date, \
                            you may have to pay up to a $40 late fee and your APRs may be increased up to \
                            the Penalty APR of 29.24%'),
                    ], className='balance'),
                    html.Section([
                        html.Div([
                            html.H3('Reward Dollars'),
                            html.H4(id='today'),
                            html.H3(id='reward_dollars')
                        ]),
                        html.Div([
                            html.H3('Credit Limit'),
                            html.H4(id='credit_limit'),
                            html.H3('Available Credit'),
                            html.H4(id='available_credit')
                        ], className='credit')
                    ], className='summary'),
                ], className='bill_statement'),
                html.Div([
                    html.Div([
                        html.Section([
                            html.Div([
                                html.P(id='name'),
                                html.P(id='street'),
                                html.P(id='zip')
                            ]),
                            html.Div([
                                html.P('$_______________.______'),
                                html.P('Amount Enclosed'),
                            ])
                        ], className='cust_address'),
                        html.Section([
                            html.Div([
                                html.P(id='bank_name'),
                                html.P(id='bank_street'),
                                html.P(id='bank_zip')
                            ])
                        ], className='bank_address'), 
                    ], className='check')
                ], className='check_container'),
                html.Div([
                    html.Div([
                        html.Section([
                            html.H3('Transactions')
                        ]),
                        dash_table.DataTable(id='monthly_activity', 
                                             page_size=10,
                                             style_as_list_view=True,
                                             style_header={'fontWeight': 'bold'},
                                             style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'})
                    ], className='monthly_transactions')
                ], className='monthly_transactions_container')
            ]),
            html.Aside([
                dash_table.DataTable(months_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in months_df],
                                        id='month',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '300px','overflowY': 'auto'}),
                html.Br(),
                dash_table.DataTable(years_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in years_df],
                                        id='year',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '150px','overflowY': 'auto'})
            ], className='sidebar')
        ], className='container')
    ], className='main_container')
], className='bill')
#----------------------------------------------------------------------------------------------------------
# update customer bill based on user input - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    [Output('err', 'children'), Output('new_balance', 'children'), Output('minimum_payment', 'children'), Output('due_date', 'children'),
     Output('today', 'children'), Output('reward_dollars', 'children'), Output('credit_limit', 'children'), 
     Output('available_credit', 'children'), Output('name', 'children'), Output('street', 'children'), 
     Output('zip', 'children'), Output('bank_name', 'children'), Output('bank_street', 'children'), 
     Output('bank_zip', 'children'), Output('monthly_activity', 'data')], 
    [Input('cc', 'value'), Input('month', 'active_cell'), Input('year', 'active_cell')] 
)
def update_bill(cc, month, year):
    if cc and month and year:
        # check if text is numeric
        if cc.isnumeric() != True:
            return ['(Please enter only numbers)','', '', '', '', '', '', '', '', '', '', '', '', '', None]
        else:
            # filter by credit card number
            cc_transactions = merged_df['CREDIT_CARD_NO'] == cc
            if merged_df[cc_transactions].empty:
                return ['(No credit card found with this number...please try again)','', '', '', '', '', '', '', '', '', '', '', '', '', None]
            
            # filter by month
            month_cell_value = months_df.iloc[month['row']].values[0]
            month_target = pd.to_datetime(merged_df['TIMEID']).dt.month == month_cell_value
            # filter by year
            year_cell_value = years_df.iloc[year['row']].values[0]
            year_target = pd.to_datetime(merged_df['TIMEID']).dt.year == year_cell_value
            # filter by month and year
            common_target = month_target.isin(year_target)

            # used to calculate all output values
            filtered_merged_df = merged_df[cc_transactions & common_target]
            # if there are no transactions for that month
            if filtered_merged_df.empty:
                return ['','$0.00', '', '', '', '', '', '', '', '', '', '', '', '', None]

            # calculate the output values to display in bill
            new_balance = filtered_merged_df['TRANSACTION_VALUE'].sum()
            minimum_payment = '$40.00'
            # fixed bug when clicking on month 12 - need to increment year by 1 + reset month to 1
            if month_cell_value == 12:
                due_date = datetime.strptime(f'{year_cell_value + 1}-01-01', '%Y-%m-%d').date()
            else:
                due_date = datetime.strptime(f'{year_cell_value}-{month_cell_value + 1}-01', '%Y-%m-%d').date()
            today = datetime.strptime(f'{year_cell_value}-{month_cell_value}-01', '%Y-%m-%d').date()
            rewards = new_balance * 0.02
            credit_limit = 10000
            available_credit = credit_limit - new_balance
            
            # select 1 row to collect customer details + bank details
            target_row = filtered_merged_df.iloc[0]
            name = f'{target_row["FIRST_NAME"]} {target_row["LAST_NAME"]}' 
            street = target_row['FULL_STREET_ADDRESS'].split(',')
            street = f'{street[1]} {street[0]}'
            zip = f'{target_row["CUST_CITY"]}, {target_row["CUST_STATE"]} {target_row["CUST_ZIP"]}'
            bank_name = target_row["BRANCH_NAME"]
            bank_street = target_row["BRANCH_STREET"]
            bank_zip = f'{target_row["BRANCH_CITY"]}, {target_row["BRANCH_STATE"]} {target_row["BRANCH_ZIP"]}'

            # monthly transactions
            rearranged_df = filtered_merged_df[['TIMEID', 'TRANSACTION_TYPE', 'TRANSACTION_VALUE']]
            rearranged_df = rearranged_df.sort_values('TIMEID', ascending=False)

            return ['',
                    f'${new_balance:,.2f}', 
                    minimum_payment, 
                    due_date, 
                    f'(as of {today})', 
                    f'${rewards:.2f}', 
                    f'${credit_limit:,.2f}', 
                    f'${available_credit:,.2f}', 
                    name, 
                    street, 
                    zip, 
                    bank_name, 
                    bank_street, 
                    bank_zip, 
                    rearranged_df.to_dict('records')]
    else:
        # defaults - when the page first loads 
        return ['','', '', '', '', '', '', '', '', '', '', '', '', '', None]
    