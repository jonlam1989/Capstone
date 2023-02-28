import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True) # need suppress callback exception for the edit existing customer details form

app.layout = html.Main([
	html.Div([
        html.H1('Sales Dashboard'),
        html.Div([
            html.Div(
                dcc.Link(f"{page['name']}", href=page["relative_path"])
            )
            for page in dash.page_registry.values()
        ])
    ], className='nav'),
	dash.page_container
], className='app')

if __name__ == '__main__':
	app.run_server(debug=True)                                           # for code reloading / hot reloading