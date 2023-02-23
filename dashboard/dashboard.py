import numpy as np
import pandas as pd

import plotly.express as px 
import plotly.graph_objects as go 
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# Used to display the transactions made by customers living in a given zip code for a given month and year. 
# Order by day in descending order.

# read cleaned data + filter for only the SSN (need this to merge dataframes) and CUST_ZIP
customer_df = pd.read_csv('cleaned_files/cleaned_customer.csv')
customer_df = customer_df[['SSN', 'CUST_ZIP']]

# read cleaned data + rename column (need this to merge dataframes)
credit_card_df = pd.read_csv('cleaned_files/cleaned_credit.csv')
credit_card_df.rename(columns={'CUST_SSN':'SSN'}, inplace=True)

# merge both dataframes
merged_df = credit_card_df.merge(customer_df, on='SSN')
# drop SSN - customer privacy
merged_df.drop(columns=['SSN'], inplace=True)
# convert column TIMEID to date type
merged_df['TIMEID'] = pd.to_datetime(merged_df['TIMEID'].astype(str), format='%Y%m%d')
# keep only the date (not the timezone)
merged_df['TIMEID'] = merged_df['TIMEID'].dt.date 

# find unique zipcodes
list_of_zipcodes = merged_df['CUST_ZIP'].sort_values().unique()
zipcodes_df = pd.DataFrame(list_of_zipcodes, columns=['List of Zip Codes'])
#----------------------------------------------------------------------------------------------------------
# Plotly Dash App
app = Dash(__name__)

app.layout = html.Main([
                html.Section([
                    html.H1('Customer Transactions'),
                    html.Br(),
                    html.Div([
                        html.Div([
                            dash_table.DataTable(merged_df.to_dict('records'),                              # https://dash.plotly.com/datatable
                                                [{'name': i, 'id': i} for i in merged_df.columns], 
                                                page_size=10, 
                                                id='data_table',
                                                style_as_list_view=True,
                                                style_header={'fontWeight': 'bold'},
                                                style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'}),
                        ], className='data'),
                        html.Div([
                            dash_table.DataTable(zipcodes_df.to_dict('records'), 
                                                 [{'name': i, 'id': i} for i in zipcodes_df],
                                                 id='zipcode_list',
                                                 page_size=50, 
                                                 style_header={'fontWeight': 'bold'}, 
                                                 style_table={'height': '300px','overflowY': 'auto'})
                        ], className='data_sidebar')
                    ], className='container')
                ], className='section')
            ], className='main')

@app.callback(
    Output('data_table', 'data'), 
    [Input('zipcode_list', 'active_cell')] 
)
def update_data_table(active_cell):
    # find the value of the active_cell 
    active_cell_value = zipcodes_df.iloc[active_cell['row']].values[0]
    # filter only for zipcodes that match the active_cell_value
    target = merged_df['CUST_ZIP'] == active_cell_value
    filtered_df = merged_df[target]
    # sort by day in descending order
    filtered_df.sort_values('TIMEID', ascending=False, inplace=True)
    # needs to match the data in data_table
    return filtered_df.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)                                                                              # for code reloading / hot reloading