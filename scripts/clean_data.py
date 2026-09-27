"""
One-time (rerunnable) cleaning pipeline: merges the ClimateBERT scoring output
with the Loughran-McDonald + FinBERT tone/readability output into a single
canonical dataset, resolving filename-level duplicates and Year/Quarter
parsing errors along the way.

Run: python scripts/clean_data.py
Output: data/clean_transcripts.csv

See PROJECT_LOG.md (Section 9) for the column dictionary and the caveats
this script documents (interim duplicate-resolution policy, unparseable
rows, approximated metrics on merged duplicate groups).
"""

import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "clean_transcripts.csv"

CLIMATE_FILE = RAW_DIR / "ClimateBert_Scores_Output_Updated.csv"
TONE_FILE = RAW_DIR / "merged_quarterly_transcripts_results_new.csv"

VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}
MIN_YEAR = 2000
MAX_YEAR = datetime.date.today().year + 1

RAW_SUM_COLS = [
    "Total_Sentences",
    "Climate_Sentences_Count",
    "Sentiment_Risk_Count",
    "Sentiment_Opportunity_Count",
    "Sentiment_Neutral_Count",
    "Positive_Count",
    "Negative_Count",
    "Uncertain_Count",
    "Weak_Modal_Count",
    "Total_Words",
    "File_Size_MB",
]

WEIGHTED_AVG_COLS = [
    "FinBERT_Positive",
    "FinBERT_Negative",
    "FinBERT_Neutral",
    "FinBERT_Tone",
    "Fog_Index",
]

FINAL_COLUMNS = [
    "Security_Code",
    "Company_Name",
    "NSE_Name",
    "Year",
    "Quarter",
    "parse_ok",
    "n_source_files",
    "Filenames",
    "duplicate_group",
    "has_climate_data",
    "climate_file_coverage",
    "Total_Sentences",
    "Climate_Sentences_Count",
    "Sentiment_Risk_Count",
    "Sentiment_Opportunity_Count",
    "Sentiment_Neutral_Count",
    "Climate_Exposure_Score",
    "Positive_Count",
    "Negative_Count",
    "Uncertain_Count",
    "Weak_Modal_Count",
    "Total_Words",
    "Tone_Score",
    "Percent_Uncertain",
    "Percent_Weak_Modal",
    "File_Size_MB",
    "File_Size_Readability",
    "Fog_Index",
    "FinBERT_Positive",
    "FinBERT_Negative",
    "FinBERT_Neutral",
    "FinBERT_Tone",
]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    cb = pd.read_csv(CLIMATE_FILE, dtype={"Security_Code": "Int64"})
    mq = pd.read_csv(TONE_FILE, dtype={"Company_ID": "Int64"})
    print(f"[load_raw] climate rows={len(cb)}  tone rows={len(mq)}")
    return cb, mq


def merge_sources(cb: pd.DataFrame, mq: pd.DataFrame) -> pd.DataFrame:
    mq = mq.rename(columns={"Company_ID": "Security_Code_mq", "Year": "Year_lm", "Quarter": "Quarter_lm"})
    cb = cb.rename(columns={"Year": "Year_cb", "Quarter": "Quarter_cb"})

    merged = mq.merge(
        cb,
        how="left",
        left_on="File_Name",
        right_on="Filename",
        suffixes=("", "_cb_dup"),
    )

    # Security_Code: prefer the tone file's Company_ID (present for every row),
    # fall back to the climate file's Security_Code as a sanity check.
    merged["Security_Code"] = merged["Security_Code_mq"].fillna(merged["Security_Code"])
    merged["Filename"] = merged["File_Name"]
    merged["NSE_Name"] = merged.get("NSE_Name")
    merged["has_climate_data"] = merged["Total_Sentences"].notna()

    print(f"[merge_sources] merged rows={len(merged)}  has_climate_data=True: {merged['has_climate_data'].sum()}")
    return merged


def _valid_period(year, quarter) -> bool:
    if quarter not in VALID_QUARTERS:
        return False
    if pd.isna(year):
        return False
    return MIN_YEAR <= year <= MAX_YEAR


def reconcile_year_quarter(df: pd.DataFrame) -> pd.DataFrame:
    year = pd.Series(np.nan, index=df.index, dtype="float64")
    quarter = pd.Series(pd.NA, index=df.index, dtype="object")
    parse_ok = pd.Series(False, index=df.index)

    for src_year, src_quarter in (("Year_lm", "Quarter_lm"), ("Year_cb", "Quarter_cb")):
        candidate_ok = (~parse_ok) & df.apply(
            lambda r, sy=src_year, sq=src_quarter: _valid_period(r[sy], r[sq]), axis=1
        )
        year[candidate_ok] = df.loc[candidate_ok, src_year]
        quarter[candidate_ok] = df.loc[candidate_ok, src_quarter]
        parse_ok[candidate_ok] = True

    df["Year"] = year.astype("Int64")
    df["Quarter"] = quarter
    df["parse_ok"] = parse_ok

    print(f"[reconcile_year_quarter] parse_ok=True: {parse_ok.sum()}  parse_ok=False: {(~parse_ok).sum()}")
    return df


def resolve_duplicates(df: pd.DataFrame, policy: str = "sum_recompute") -> pd.DataFrame:
    """
    Groups rows sharing (Security_Code, Year, Quarter) among parse_ok=True rows
    and combines them into a single row per company-period.

    INTERIM POLICY, pending confirmation from the user: the meaning of the
    odd-numbered filename suffixes (_1/_3/_5/_7/_9) that create these
    duplicate groups is not yet known (no local access to the raw source
    transcripts to check). "sum_recompute" sums raw countable metrics and
    recomputes derived ratios from the sums, and weighted-averages the
    metrics that can't be exactly reconstructed (FinBERT_*, Fog_Index).
    This function is the single place to change if that assumption turns
    out to be wrong.
    """
    if policy != "sum_recompute":
        raise ValueError(f"Unknown duplicate-resolution policy: {policy}")

    passthrough = df[~df["parse_ok"]].copy()
    passthrough["n_source_files"] = 1
    passthrough["Filenames"] = passthrough["Filename"]
    passthrough["duplicate_group"] = False
    passthrough["climate_file_coverage"] = passthrough["has_climate_data"].astype(float)

    groupable = df[df["parse_ok"]].copy()
    group_keys = ["Security_Code", "Year", "Quarter"]

    static_cols = ["Company_Name", "NSE_Name"]

    rows = []
    for key, g in groupable.groupby(group_keys, dropna=False):
        out = {"Security_Code": key[0], "Year": key[1], "Quarter": key[2]}
        out["parse_ok"] = True
        out["n_source_files"] = len(g)
        out["Filenames"] = ";".join(g["Filename"].tolist())
        out["duplicate_group"] = len(g) > 1
        out["has_climate_data"] = bool(g["has_climate_data"].any())
        out["climate_file_coverage"] = float(g["has_climate_data"].mean())

        for col in static_cols:
            out[col] = g[col].dropna().iloc[0] if g[col].notna().any() else pd.NA

        for col in RAW_SUM_COLS:
            out[col] = g[col].sum(skipna=True)

        weights = g["Total_Words"].fillna(0)
        total_weight = weights.sum()
        for col in WEIGHTED_AVG_COLS:
            vals = g[col]
            mask = vals.notna() & (weights > 0)
            if mask.any() and total_weight > 0:
                out[col] = float((vals[mask] * weights[mask]).sum() / weights[mask].sum())
            else:
                out[col] = np.nan

        rows.append(out)

    resolved = pd.DataFrame(rows)
    # passthrough already carries every raw column needed (it's an unmodified
    # slice of df); just select the same columns resolved has, in that order.
    passthrough = passthrough[resolved.columns]
    combined = pd.concat([resolved, passthrough], ignore_index=True, sort=False)

    n_dupe_groups = int(resolved["duplicate_group"].sum())
    print(f"[resolve_duplicates] output rows={len(combined)}  duplicate_group=True: {n_dupe_groups}  passthrough(parse_ok=False): {len(passthrough)}")
    return combined


def recompute_exact_ratios(df: pd.DataFrame) -> pd.DataFrame:
    def safe_div(numerator, denominator):
        denom = denominator.replace(0, np.nan)
        return numerator / denom

    df["Climate_Exposure_Score"] = safe_div(df["Climate_Sentences_Count"], df["Total_Sentences"]) * 100
    # Guarded like the other ratios (NaN, not 0.0, when Positive+Negative==0) so a
    # zero-word extraction-failure transcript doesn't masquerade as a real "neutral" score.
    df["Tone_Score"] = safe_div(
        df["Positive_Count"] - df["Negative_Count"], df["Positive_Count"] + df["Negative_Count"]
    )
    df["Percent_Uncertain"] = safe_div(df["Uncertain_Count"], df["Total_Words"]) * 100
    df["Percent_Weak_Modal"] = safe_div(df["Weak_Modal_Count"], df["Total_Words"]) * 100
    df["File_Size_Readability"] = -np.log(df["File_Size_MB"] + 1)

    print("[recompute_exact_ratios] done")
    return df


def finalize_and_save(df: pd.DataFrame) -> pd.DataFrame:
    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    out = df[FINAL_COLUMNS].sort_values(["Security_Code", "Year", "Quarter"], na_position="last")
    out.to_csv(OUT_PATH, index=False)

    print(f"[finalize_and_save] wrote {len(out)} rows to {OUT_PATH}")
    print(f"  parse_ok=False: {(~out['parse_ok']).sum()}")
    print(f"  duplicate_group=True: {out['duplicate_group'].sum()}")
    print(f"  has_climate_data=False: {(~out['has_climate_data']).sum()}")
    return out


def main():
    cb, mq = load_raw()
    merged = merge_sources(cb, mq)
    merged = reconcile_year_quarter(merged)
    resolved = resolve_duplicates(merged, policy="sum_recompute")
    resolved = recompute_exact_ratios(resolved)
    finalize_and_save(resolved)


if __name__ == "__main__":
    main()
