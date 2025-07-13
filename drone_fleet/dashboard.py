"""Dashboard for visualizing fleet metrics."""

try:
    import dash
    from dash import html, dcc
except ImportError:  # pragma: no cover
    dash = None
    html = dcc = None  # type: ignore


def create_dashboard() -> 'dash.Dash':
    if dash is None:
        raise ImportError("Dash is required for the dashboard")
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.H1("Drone Fleet Dashboard"),
        dcc.Graph(id="routes"),
    ])
    return app
