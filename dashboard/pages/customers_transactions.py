import numpy as np
import pandas as pd

import mysql.connector as mariadb
from dotenv import load_dotenv              # environment variables
import os

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# 1. Used to display the transactions made by customers living in a given zip code for a given month and year. 
#    (Order by day in descending order.)
# 2. Used to display the number and total values of transactions for a given type.
# 3. Used to display the number and total values of transactions for branches in a given state.
#----------------------------------------------------------------------------------------------------------
# load the environment variables
load_dotenv()

# assign environment variables
PASSWORD = os.getenv('MariaDB_Password')
USER = os.getenv('MariaDB_Username')

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
#----------------------------------------------------------------------------------------------------------
# read cleaned data + filter for only the SSN (need this to merge dataframes) and CUST_ZIP
customer_df = get_customer_data()
customer_df = customer_df[['SSN', 'CUST_ZIP', 'CUST_STATE']]

# read cleaned data + rename column (need this to merge dataframes)
credit_card_df = get_credit_data()
credit_card_df.rename(columns={'CUST_SSN':'SSN'}, inplace=True)

# merge both dataframes
merged_df = credit_card_df.merge(customer_df, on='SSN')
merged_df.drop(columns=['SSN'], inplace=True)
merged_df['TIMEID'] = pd.to_datetime(merged_df['TIMEID'], format='%Y%m%d')
merged_df['TIMEID'] = merged_df['TIMEID'].dt.date 

# dropdown label
transaction_type = merged_df['TRANSACTION_TYPE'].unique()
transaction_type_options = [{'label': type, 'value': type} for type in transaction_type]
# state label
state = merged_df['CUST_STATE'].unique()
state.sort()
state_options = [{'label': s, 'value': s} for s in state]

# find unique zipcodes
list_of_zipcodes = merged_df['CUST_ZIP'].sort_values().unique()
zipcodes_df = pd.DataFrame(list_of_zipcodes, columns=['Filter by Zip Code'])
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
dash.register_page(__name__, path='/')

layout = html.Main([
    html.Div([
        html.H2('All Customer Transactions'),
        html.Div([
            html.Section([
                dash_table.DataTable(merged_df.to_dict('records'),          # https://dash.plotly.com/datatable
                                    [{'name': i, 'id': i} for i in merged_df.columns], 
                                    page_size=10, 
                                    id='data_table',
                                    style_as_list_view=True,
                                    style_header={'fontWeight': 'bold'},
                                    style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'}),
                html.Div([
                    html.Section([
                        html.Div([
                            html.Section([
                                html.P('Transactions'),
                                html.P(id='transaction_number', children=['0'])
                            ]),
                            html.Section([
                                html.P('Total Dollars'),
                                html.P(id='transaction_dollars', children=['$0'])
                            ])
                        ], className='values'),
                        dcc.Dropdown(
                            id='transaction_type',
                            className='dropdown',
                            placeholder='Select a transaction type',
                            options=transaction_type_options,
                            maxHeight=100
                        )], className='values_container'),
                    html.Section([
                        html.Div([
                            html.Section([
                                html.P('Branches'),
                                html.P(id='branch_number', children=['0'])
                            ]),
                            html.Section([
                                html.P('Total Dollars'),
                                html.P(id='state_dollars', children=['$0'])
                            ])
                        ], className='values'),
                        dcc.Dropdown(
                            id='state',
                            className='dropdown',
                            placeholder='Select a state',
                            options=state_options,
                            maxHeight=100
                        )], className='values_container')
                ], className='stats')
            ], className='data'),
            html.Aside([
                dash_table.DataTable(zipcodes_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in zipcodes_df],
                                        id='zipcode_list',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '350px','overflowY': 'auto'}),
                html.Br(),
                dash_table.DataTable(months_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in months_df],
                                        id='months_list',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '150px','overflowY': 'auto'}),
                html.Br(),
                dash_table.DataTable(years_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in years_df],
                                        id='years_list',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '150px','overflowY': 'auto'})
            ], className='data_sidebar')
        ], className='container')
    ], className='main_container')
], className='transactions')
#----------------------------------------------------------------------------------------------------------
# update customer transaction based on user input - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    Output('data_table', 'data'), 
    [Input('zipcode_list', 'active_cell'), Input('months_list', 'active_cell'), Input('years_list', 'active_cell')] 
)
def update_data_table(zipcode_list, months_list, years_list):
    if zipcode_list == None and months_list == None and years_list == None:
        return merged_df.to_dict('records')
    else:
        # defaults to all, if end-user does not click on any filters 
        zipcode_target = merged_df['CUST_ZIP'] != None
        month_target = merged_df['TIMEID'] != None
        year_target = merged_df['TIMEID'] != None

        # filter by zipcode 
        if zipcode_list:
            zipcode_cell_value = zipcodes_df.iloc[zipcode_list['row']].values[0]
            zipcode_target = merged_df['CUST_ZIP'] == zipcode_cell_value

        # filter by month
        if months_list:
            month_cell_value = months_df.iloc[months_list['row']].values[0]
            month_target = pd.to_datetime(merged_df['TIMEID']).dt.month == month_cell_value
        
        # filter by year
        if years_list:
            year_cell_value = years_df.iloc[years_list['row']].values[0]
            year_target = pd.to_datetime(merged_df['TIMEID']).dt.year == year_cell_value
        
        # if both month filter + year filter are clicked, need to find only the ones in common in both
        if months_list and years_list:
            common_target = month_target.isin(year_target)
            filtered_df = merged_df[zipcode_target & common_target]
        elif months_list == None and years_list:
            filtered_df = merged_df[zipcode_target & year_target]
        elif months_list and years_list == None:
            filtered_df = merged_df[zipcode_target & month_target]
        else:
            filtered_df = merged_df[zipcode_target & month_target & year_target]

        filtered_df = filtered_df.sort_values('TIMEID', ascending=False)
        # needs to match the data in data_table
        return filtered_df.to_dict('records')
#----------------------------------------------------------------------------------------------------------
# update stats based on transaction type - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    [Output('transaction_number', 'children'), Output('transaction_dollars', 'children')],
    [Input('transaction_type', 'value')]
)
def update_transaction_type(transaction_type):
    # filter by transaction type
    type = merged_df['TRANSACTION_TYPE'] == transaction_type
    filtered_df = merged_df[type]
    
    # find the count + sum 
    number = filtered_df['TRANSACTION_TYPE'].count()
    dollars = filtered_df['TRANSACTION_VALUE'].sum()

    if transaction_type:
        return [number, f'${dollars:,.2f}']                                 # how to format string numbers with a comma
    return ['0', '$0']
#----------------------------------------------------------------------------------------------------------
# update stats based on state - *NEED TO CONVERT @app.callback -> @dash.callback FOR MULTI-PAGE FUNCTIONALITY*
@dash.callback(
    [Output('branch_number', 'children'), Output('state_dollars', 'children')],
    [Input('state', 'value')]
)
def update_state(state):
    # filter by state
    target_state = merged_df['CUST_STATE'] == state
    filtered_df = merged_df[target_state]
    
    # find the count + sum 
    number = len(filtered_df['BRANCH_CODE'].unique())
    dollars = filtered_df['TRANSACTION_VALUE'].sum()

    if state:
        return [number, f'${dollars:,.2f}']                                  # how to format string numbers with a comma
    return ['0', '$0']
