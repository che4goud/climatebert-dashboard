import streamlit as st
from lib.charts import line_over_time
from lib.data import company_options, load_data

st.set_page_config(page_title="Company Explorer", page_icon="🔍", layout="wide")
st.title("Company Explorer")

df = load_data()
options = company_options(df)

label = st.selectbox("Search or select a company", options["company_label"], index=0)
security_code = options.loc[options["company_label"] == label, "Security_Code"].iloc[0]

company_rows = df[df["Security_Code"] == security_code]
parsed = company_rows[company_rows["parse_ok"]].sort_values("period_sort")
unparsed = company_rows[~company_rows["parse_ok"]]

st.caption(f"{len(company_rows)} transcript(s) on record for this company.")

climate_rows = parsed[parsed["has_climate_data"]]

metrics = [
    ("Climate_Exposure_Score", "Climate Exposure (%)", climate_rows),
    ("Tone_Score", "Financial Tone", parsed),
    ("FinBERT_Tone", "FinBERT Tone", parsed),
    ("Fog_Index", "Fog Index (Readability)", parsed),
]

if climate_rows.empty:
    st.info(
        "No climate-scored transcripts are available for this company — every transcript on record "
        "either predates climate scoring coverage or hit a text-extraction failure upstream. Financial "
        "tone and readability trends are still shown below where available.",
        icon="ℹ️",
    )

row1 = st.columns(2)
row2 = st.columns(2)
slots = row1 + row2

for (metric, label_text, data), slot in zip(metrics, slots):
    with slot:
        st.subheader(label_text)
        if data.empty or data[metric].dropna().empty:
            st.caption("No data available for this metric.")
        else:
            fig = line_over_time(data, metric, label_text, hover_cols=["n_source_files", "duplicate_group"])
            st.plotly_chart(fig, width="stretch")

st.divider()

if not unparsed.empty:
    st.subheader("Excluded from charts above (fiscal period could not be determined)")
    st.dataframe(unparsed[["Filenames"]], width="stretch", hide_index=True)

st.subheader("All contributing transcript rows")
display_cols = [
    "Year", "Quarter", "n_source_files", "duplicate_group", "has_climate_data",
    "Climate_Exposure_Score", "Tone_Score", "FinBERT_Tone", "Fog_Index",
    "Total_Words", "Filenames",
]
display_cols = [c for c in display_cols if c in company_rows.columns]
st.dataframe(
    company_rows.sort_values("period_sort")[display_cols],
    width="stretch", hide_index=True,
)
