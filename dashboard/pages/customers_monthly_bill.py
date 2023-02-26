import numpy as np
import pandas as pd

from datetime import datetime

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
            html.Section([
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
    [Output('new_balance', 'children'), Output('minimum_payment', 'children'), Output('due_date', 'children'),
     Output('today', 'children'), Output('reward_dollars', 'children'), Output('credit_limit', 'children'), 
     Output('available_credit', 'children')],
    [Input('cc', 'value'), Input('month', 'active_cell'), Input('year', 'active_cell')] 
)
def update_bill(cc, month, year):
    if cc and month and year:
        # filter by month
        month_cell_value = months_df.iloc[month['row']].values[0]
        month_target = pd.to_datetime(merged_df['TIMEID']).dt.month == month_cell_value
        # filter by year
        year_cell_value = years_df.iloc[year['row']].values[0]
        year_target = pd.to_datetime(merged_df['TIMEID']).dt.year == year_cell_value
        
        # filter by month and year
        common_target = month_target.isin(year_target)
        # filter by credit card number
        cc_transactions = merged_df['CREDIT_CARD_NO'] == int(cc)
        
        filtered_merged_df = merged_df[cc_transactions & common_target]
        # print(filtered_merged_df)
        
        # calculate the output values
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

        return [f'${new_balance:,.2f}', 
                minimum_payment, 
                due_date, 
                f'as of {today}', 
                f'${rewards:.2f}', 
                f'${credit_limit:,.2f}', 
                f'${available_credit:,.2f}']
    else:
        # defaults - when the page first loads 
        return ['', '', '', '', '', '', '']