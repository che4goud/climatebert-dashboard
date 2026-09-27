import pandas as pd
import streamlit as st
from lib.data import load_data

st.set_page_config(page_title="About the Data", page_icon="📖", layout="wide")
st.title("About the Data")

df = load_data()

st.subheader("Where the numbers come from")
st.markdown(
    "This dashboard is built on two independently produced datasets, both scored at the level of a "
    "single quarterly earnings-call transcript for BSE-listed companies:\n\n"
    "- **Climate exposure & sentiment** — a transformer-based language model further trained on climate "
    "news, research abstracts, and corporate sustainability reports classifies each sentence as "
    "climate-related or not, and each climate-related sentence as framed by *risk*, *opportunity*, or "
    "*neutral* language.\n"
    "- **Financial tone, hedging & readability** — the Loughran-McDonald finance-specific word dictionary "
    "counts positive, negative, uncertain, and weak-modal (hedging) language; FinBERT provides an "
    "independent model-based sentiment read; and the Gunning Fog Index measures readability.\n\n"
    "Both datasets are merged once by a cleaning script into the single canonical dataset this dashboard "
    "reads — no cleaning happens live in the app itself."
)

st.subheader("Data-quality notes")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total rows", f"{len(df):,}")
c2.metric("Combined multi-file rows", f"{df['duplicate_group'].sum():,}")
c3.metric("Excluded from time charts", f"{(~df['parse_ok']).sum():,}")
c4.metric("No climate score", f"{(~df['has_climate_data']).sum():,}")

st.markdown(
    "- **Combined multi-file rows** — some company-quarters are represented by more than one source "
    "transcript file. These are summed together and their ratio-based metrics recomputed exactly; "
    "FinBERT and Fog Index scores on these rows are a word-count-weighted average across the "
    "contributing files rather than an exact recomputation, since they aren't simple ratios of countable "
    "quantities. What these duplicate files actually represent (e.g. separate call segments vs. "
    "re-uploads) has not yet been confirmed against source recordings — this is an interim policy.\n"
    "- **Excluded from time charts** — a small number of transcripts could not be assigned a reliable "
    "fiscal year/quarter from their filename. They are kept in the dataset (visible on the Company "
    "Explorer page) but left out of any year/quarter-based chart or filter.\n"
    "- **No climate score** — a handful of transcripts hit a text-extraction failure upstream of both "
    "scoring pipelines and carry zero counts across every metric; they're flagged rather than dropped."
)

st.subheader("Column reference")

SCHEMA = [
    ("Security_Code", "BSE company identifier."),
    ("Company_Name / NSE_Name", "Company name and short ticker-style name."),
    ("Year / Quarter", "Reconciled fiscal period."),
    ("parse_ok", "Whether a valid fiscal period could be established for this row."),
    ("n_source_files", "Number of original transcript files combined into this row."),
    ("Filenames", "Every source filename contributing to this row."),
    ("duplicate_group", "Whether this row combines more than one source file."),
    ("has_climate_data", "Whether a climate score exists for this row."),
    ("climate_file_coverage", "Fraction of contributing files that had a climate score."),
    ("Climate_Exposure_Score", "% of transcript sentences that are climate-related."),
    ("Sentiment_Risk_Count / Sentiment_Opportunity_Count / Sentiment_Neutral_Count", "Climate sentences framed as risk / opportunity / neutral."),
    ("Tone_Score", "Net Loughran-McDonald sentiment: (positive − negative) / (positive + negative)."),
    ("Percent_Uncertain / Percent_Weak_Modal", "Share of words flagged as hedging/uncertain language."),
    ("Total_Words", "Word count of the (combined, if applicable) transcript."),
    ("Fog_Index", "Gunning Fog readability score (~12 = high school, ~16 = college, 18+ = graduate)."),
    ("FinBERT_Positive / FinBERT_Negative / FinBERT_Neutral", "FinBERT model class probabilities."),
    ("FinBERT_Tone", "Net FinBERT sentiment (Positive − Negative)."),
]
st.dataframe(pd.DataFrame(SCHEMA, columns=["Column", "Description"]), width="stretch", hide_index=True)

st.caption(
    "A full process document — covering both raw source datasets column-by-column, the seven-step "
    "cleaning pipeline, and this column-to-dashboard mapping in detail — is maintained alongside this "
    "project as Process_Documentation.pdf."
)
