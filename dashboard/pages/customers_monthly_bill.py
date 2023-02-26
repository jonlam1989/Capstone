import numpy as np
import pandas as pd

import dash
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# 1. Used to generate a monthly bill for a credit card number for a given month and year.
#----------------------------------------------------------------------------------------------------------
# read cleaned data
customer_df = pd.read_csv('cleaned_files/cleaned_customer.csv')
credit_card_df = pd.read_csv('cleaned_files/cleaned_credit.csv')
branch_df = pd.read_csv('cleaned_files/cleaned_branch.csv')
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
        html.Div(id='error'),
        html.Div([
            html.Section([], className='bill_statement'),
            html.Aside([
                dash_table.DataTable(months_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in months_df],
                                        id='months_list',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '300px','overflowY': 'auto'}),
                html.Br(),
                dash_table.DataTable(years_df.to_dict('records'), 
                                        [{'name': i, 'id': i} for i in years_df],
                                        id='years_list',
                                        style_header={'fontWeight': 'bold'}, 
                                        style_table={'height': '150px','overflowY': 'auto'})
            ], className='sidebar')
        ], className='container')
    ], className='main_container')
], className='bill')
#----------------------------------------------------------------------------------------------------------
