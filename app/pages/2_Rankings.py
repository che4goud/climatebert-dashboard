import streamlit as st
from lib.charts import horizontal_bar
from lib.constants import METRIC_LABELS, QUARTER_ORDER
from lib.data import aggregate_by_company, filter_by_period, load_data

st.set_page_config(page_title="Rankings", page_icon="🏆", layout="wide")
st.title("Rankings")

df = load_data()
parsed = df[df["parse_ok"]]

year_min, year_max = int(parsed["Year"].min()), int(parsed["Year"].max())

with st.sidebar:
    st.header("Filters")
    year_range = st.slider("Year range", year_min, year_max, (year_min, year_max))
    quarters = st.multiselect("Quarters", QUARTER_ORDER, default=QUARTER_ORDER)
    metric = st.selectbox(
        "Rank by", list(METRIC_LABELS.keys()),
        format_func=lambda c: METRIC_LABELS[c][0],
    )
    direction = st.radio("Direction", ["Top", "Bottom"], horizontal=True)
    top_n = st.slider("Number of companies", 5, 50, 10)
    min_periods = st.number_input("Minimum quarters of data in range", min_value=1, value=2, step=1)

st.caption(METRIC_LABELS[metric][1])

filtered = filter_by_period(df, year_range=year_range, quarters=quarters)
agg = aggregate_by_company(filtered, metric, agg="mean", min_periods=min_periods)

if agg.empty:
    st.warning("No companies meet the current filters. Try lowering the minimum-quarters requirement.")
else:
    ranked = agg.sort_values("value", ascending=(direction == "Bottom")).head(top_n)
    label_text = METRIC_LABELS[metric][0]

    st.plotly_chart(
        horizontal_bar(ranked, "company_label", "value", label_text),
        width="stretch",
    )

    st.dataframe(
        ranked.rename(columns={
            "company_label": "Company", "value": label_text, "n_periods": "Quarters of data",
        })[["Company", label_text, "Quarters of data"]],
        width="stretch", hide_index=True,
    )
