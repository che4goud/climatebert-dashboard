import streamlit as st
from lib.charts import histogram, year_bar
from lib.data import load_data

st.set_page_config(page_title="Climate & Tone Analytics", page_icon="🌍", layout="wide")

df = load_data()
parsed = df[df["parse_ok"]]
climate = parsed[parsed["has_climate_data"]]

st.title("Climate Risk & Financial Tone Analytics")
st.caption(
    "Quarterly earnings-call analysis of BSE-listed companies: climate exposure/sentiment "
    "(ClimateBERT) alongside financial tone, hedging, and readability (Loughran-McDonald + FinBERT)."
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Companies", f"{df['Security_Code'].nunique():,}")
c2.metric("Transcripts", f"{len(df):,}")
c3.metric("Year range", f"{int(parsed['Year'].min())}–{int(parsed['Year'].max())}")
c4.metric("Dated & usable", f"{df['parse_ok'].mean() * 100:.1f}%")
c5.metric("Climate-scored", f"{df['has_climate_data'].mean() * 100:.1f}%")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Climate Exposure distribution")
    st.plotly_chart(histogram(climate, "Climate_Exposure_Score", "Climate Exposure (%)"),
                     width="stretch")
with col2:
    st.subheader("Financial Tone distribution")
    st.plotly_chart(histogram(parsed, "Tone_Score", "Tone Score"), width="stretch")

st.subheader("Transcripts covered per year")
st.plotly_chart(year_bar(parsed), width="stretch")

st.info(
    "**Data caveats:** ~3% of transcripts could not be assigned a reliable fiscal period and are "
    "excluded from year/quarter-based views; a small number lack a climate score due to an upstream "
    "text-extraction failure; some company-quarters combine more than one source file under an interim "
    "policy. See the **About Data** page for full detail.",
    icon="ℹ️",
)
