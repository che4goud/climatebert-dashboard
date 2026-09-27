import plotly.express as px
import plotly.graph_objects as go

PRIMARY = "#28623D"
SECONDARY = "#8C6D1F"
ACCENT = "#3D8361"


def line_over_time(df, y_col, label, hover_cols=None):
    df = df.sort_values("period_sort")
    fig = px.line(
        df, x="period_label", y=y_col, markers=True,
        labels={"period_label": "Period", y_col: label},
        hover_data=hover_cols or [],
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_xaxes(categoryorder="array", categoryarray=df["period_label"].tolist())
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=280)
    return fig


def histogram(df, col, label, color=PRIMARY):
    fig = px.histogram(df, x=col, labels={col: label}, color_discrete_sequence=[color])
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320, bargap=0.05)
    return fig


def year_bar(df):
    counts = df["Year"].value_counts().sort_index()
    fig = px.bar(x=counts.index.astype(str), y=counts.values,
                 labels={"x": "Year", "y": "Transcripts"},
                 color_discrete_sequence=[ACCENT])
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
    return fig


def horizontal_bar(df, label_col, value_col, value_label):
    fig = px.bar(
        df.sort_values(value_col), x=value_col, y=label_col, orientation="h",
        labels={value_col: value_label, label_col: "Company"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=max(320, 28 * len(df)))
    return fig


def corr_heatmap(corr_df):
    fig = px.imshow(
        corr_df, text_auto=".2f", color_continuous_scale="RdYlGn", zmin=-1, zmax=1,
        aspect="auto",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=450)
    return fig


def scatter(df, x_col, y_col, x_label, y_label, color_col=None, hover_name=None):
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, hover_name=hover_name,
        labels={x_col: x_label, y_col: y_label},
        opacity=0.65, color_continuous_scale="Viridis" if color_col else None,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=480)
    return fig
