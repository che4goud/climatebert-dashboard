"""Invariant checks on data/clean_transcripts.csv, the cleaning script's output.

Run: pytest tests/test_clean_data.py
"""

from pathlib import Path

import pandas as pd
import pytest

CLEAN_PATH = Path(__file__).resolve().parent.parent / "data" / "clean_transcripts.csv"


@pytest.fixture(scope="module")
def clean_df():
    if not CLEAN_PATH.exists():
        pytest.skip("data/clean_transcripts.csv not generated yet — run scripts/clean_data.py first")
    return pd.read_csv(CLEAN_PATH)


def test_no_duplicate_periods_among_parsed_rows(clean_df):
    ok = clean_df[clean_df["parse_ok"]]
    dupes = ok.duplicated(subset=["Security_Code", "Year", "Quarter"]).sum()
    assert dupes == 0


def test_sentiment_counts_sum_to_climate_sentences(clean_df):
    sub = clean_df[clean_df["has_climate_data"]]
    total = sub["Sentiment_Risk_Count"] + sub["Sentiment_Opportunity_Count"] + sub["Sentiment_Neutral_Count"]
    assert (abs(total - sub["Climate_Sentences_Count"]) < 1e-6).all()


def test_climate_exposure_score_formula(clean_df):
    sub = clean_df[clean_df["Total_Sentences"] > 0]
    expected = sub["Climate_Sentences_Count"] / sub["Total_Sentences"] * 100
    assert (abs(expected - sub["Climate_Exposure_Score"]) < 1e-6).all()


def test_source_file_count_reconciles(clean_df):
    # Must match the combined row count of the two raw CSVs (15,812 + 15,828 - overlap
    # handled at merge time -> merged frame has 15,828 rows, one per tone-file row).
    assert clean_df["n_source_files"].sum() == 15828


def test_unparseable_rows_kept_not_dropped(clean_df):
    unparsed = clean_df[~clean_df["parse_ok"]]
    assert len(unparsed) == 20
