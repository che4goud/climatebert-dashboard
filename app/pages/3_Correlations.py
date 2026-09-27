import streamlit as st
from lib.charts import corr_heatmap, scatter
from lib.constants import DEFAULT_CORRELATION_METRICS, METRIC_LABELS, QUARTER_ORDER
from lib.data import aggregate_by_company, filter_by_period, load_data

st.set_page_config(page_title="Correlations", page_icon="📈", layout="wide")
st.title("Correlations")

df = load_data()
parsed = df[df["parse_ok"]]
year_min, year_max = int(parsed["Year"].min()), int(parsed["Year"].max())

with st.sidebar:
    st.header("Filters")
    year_range = st.slider("Year range", year_min, year_max, (year_min, year_max))
    quarters = st.multiselect("Quarters", QUARTER_ORDER, default=QUARTER_ORDER)
    include_no_climate = st.checkbox(
        "Include transcripts without a climate score", value=False,
        help="Irrelevant for climate metrics, but affects sample size for tone/readability-only comparisons.",
    )

filtered = filter_by_period(df, year_range=year_range, quarters=quarters)
if not include_no_climate:
    filtered = filtered[filtered["has_climate_data"]]

st.subheader("Correlation matrix")
metric_options = list(METRIC_LABELS.keys())
selected = st.multiselect(
    "Metrics to compare", metric_options, default=DEFAULT_CORRELATION_METRICS,
    format_func=lambda c: METRIC_LABELS[c][0],
)

if len(selected) >= 2:
    corr_df = filtered[selected].corr()
    corr_df.columns = [METRIC_LABELS[c][0] for c in corr_df.columns]
    corr_df.index = [METRIC_LABELS[c][0] for c in corr_df.index]
    st.plotly_chart(corr_heatmap(corr_df), width="stretch")
else:
    st.info("Select at least two metrics to see their correlation matrix.")

st.divider()
st.subheader("Scatter explorer")

c1, c2, c3 = st.columns(3)
with c1:
    x_metric = st.selectbox("X axis", metric_options, index=0, format_func=lambda c: METRIC_LABELS[c][0])
with c2:
    y_metric = st.selectbox("Y axis", metric_options, index=1, format_func=lambda c: METRIC_LABELS[c][0])
with c3:
    grain = st.radio("Grain", ["Per transcript", "Company average"], horizontal=False)

color_by_year = st.checkbox("Colour by year", value=True)

if grain == "Per transcript":
    plot_df = filtered.dropna(subset=[x_metric, y_metric]).copy()
    color_col = "Year" if color_by_year else None
    fig = scatter(plot_df, x_metric, y_metric, METRIC_LABELS[x_metric][0], METRIC_LABELS[y_metric][0],
                  color_col=color_col, hover_name="company_label")
else:
    x_agg = aggregate_by_company(filtered, x_metric).rename(columns={"value": "x"})[["Security_Code", "x"]]
    y_agg = aggregate_by_company(filtered, y_metric).rename(columns={"value": "y"})[["Security_Code", "company_label", "y"]]
    plot_df = x_agg.merge(y_agg, on="Security_Code")
    fig = scatter(plot_df, "x", "y", METRIC_LABELS[x_metric][0], METRIC_LABELS[y_metric][0],
                  hover_name="company_label")

st.plotly_chart(fig, width="stretch")
