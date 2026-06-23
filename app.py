from dash import Dash, html  # pyrefly: ignore [missing-import]

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Personal Finance Analyzer")
])

server = app.server

if __name__ == "__main__":
    app.run(debug=True)
