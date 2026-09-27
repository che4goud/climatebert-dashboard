QUARTER_ORDER = ["Q1", "Q2", "Q3", "Q4"]

# column -> (display name, help text)
METRIC_LABELS = {
    "Climate_Exposure_Score": (
        "Climate Exposure (%)",
        "% of transcript sentences that are climate-related.",
    ),
    "Tone_Score": (
        "Financial Tone",
        "Loughran-McDonald net tone: (positive - negative) / (positive + negative). -1 to +1.",
    ),
    "FinBERT_Tone": (
        "FinBERT Tone",
        "Model-based net sentiment from FinBERT, for comparison with the dictionary-based Tone Score.",
    ),
    "Fog_Index": (
        "Fog Index",
        "Gunning Fog readability score. ~12 = high school level, ~16 = college, 18+ = graduate.",
    ),
    "Percent_Uncertain": (
        "% Uncertain Language",
        "Share of words flagged as uncertain/hedging language (Loughran-McDonald).",
    ),
    "Percent_Weak_Modal": (
        "% Weak Modal Language",
        "Share of words flagged as weak-modal hedging language (could/might/may).",
    ),
    "Total_Words": (
        "Transcript Length (words)",
        "Total word count of the (combined, if duplicate) transcript.",
    ),
    "Climate_Sentences_Count": (
        "Climate Sentences",
        "Count of sentences classified as climate-related.",
    ),
    "Sentiment_Risk_Count": ("Risk-Framed Sentences", "Climate sentences framed as risk."),
    "Sentiment_Opportunity_Count": ("Opportunity-Framed Sentences", "Climate sentences framed as opportunity."),
    "Sentiment_Neutral_Count": ("Neutral-Framed Sentences", "Climate sentences framed as neutral."),
}

DEFAULT_CORRELATION_METRICS = [
    "Climate_Exposure_Score",
    "Tone_Score",
    "FinBERT_Tone",
    "Percent_Uncertain",
    "Fog_Index",
    "Total_Words",
]
