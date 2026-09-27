from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "clean_transcripts.csv"

QUARTER_NUM = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    df["Year"] = df["Year"].astype("Int64")
    df["Quarter"] = pd.Categorical(df["Quarter"], categories=["Q1", "Q2", "Q3", "Q4"], ordered=True)
    for col in ["parse_ok", "duplicate_group", "has_climate_data"]:
        df[col] = df[col].astype(bool)

    quarter_num = df["Quarter"].map(QUARTER_NUM).astype("float")
    df["period_sort"] = np.where(df["parse_ok"], df["Year"].astype("float") + quarter_num * 0.25, np.nan)
    df["period_label"] = np.where(
        df["parse_ok"],
        df["Year"].astype("string") + " " + df["Quarter"].astype("string"),
        "Unknown",
    )
    df["company_label"] = np.where(
        df["NSE_Name"].notna() & (df["NSE_Name"].astype("string") != ""),
        df["Company_Name"].astype("string") + " (" + df["NSE_Name"].astype("string") + ")",
        df["Company_Name"].astype("string"),
    )
    return df


def filter_by_period(df: pd.DataFrame, year_range=None, quarters=None, only_parsed=True) -> pd.DataFrame:
    out = df
    if only_parsed:
        out = out[out["parse_ok"]]
    if year_range:
        out = out[(out["Year"] >= year_range[0]) & (out["Year"] <= year_range[1])]
    if quarters:
        out = out[out["Quarter"].isin(quarters)]
    return out


def aggregate_by_company(df: pd.DataFrame, metric: str, agg: str = "mean", min_periods: int = 1) -> pd.DataFrame:
    grouped = df.dropna(subset=[metric]).groupby(
        ["Security_Code", "Company_Name", "NSE_Name", "company_label"], dropna=False
    )
    out = grouped.agg(value=(metric, agg), n_periods=(metric, "count")).reset_index()
    return out[out["n_periods"] >= min_periods].sort_values("value", ascending=False)


def company_options(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[["Security_Code", "company_label"]]
        .drop_duplicates()
        .sort_values("company_label")
        .reset_index(drop=True)
    )
