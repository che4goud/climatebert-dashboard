# ClimateBert Transcript Dashboard — Project Log

This file is the running record of what this project is, what the data looks like, and what we've decided/done so far. Update it at the end of each work session rather than relying on chat history.

---

## 1. Goal

Build an online, navigable dashboard over Indian (BSE-listed) company earnings-call transcript analysis — combining **climate-risk/opportunity exposure** (ClimateBERT) with **general financial tone/readability** (Loughran-McDonald + FinBERT), across ~1,360 companies and multiple years/quarters.

## 2. Folder Inventory

| File | Type | Role |
|---|---|---|
| `2110.12010v3ClimateBert.pdf` | Academic paper | Source method for the ClimateBERT model (Webersinke et al. 2022) — background theory only, not code we run. |
| `ppt (2).pdf` | Slide deck | Human-readable summary/study guide of the paper above. |
| `tone explanation sectionwise.pdf` | Pipeline doc | Step-by-step explanation of the Python/Colab script that produced `merged_quarterly_transcripts_results_new.csv`. |
| `ClimateBert_Scores_Output_Updated.csv` | **Data** | Output of the ClimateBERT scoring pipeline — climate exposure + risk/opportunity/neutral sentiment, one row per transcript file. |
| `merged_quarterly_transcripts_results_new.csv` | **Data** | Output of the Loughran-McDonald + FinBERT tone/readability pipeline, one row per transcript file. |

**Not in this folder:** the raw transcript `.txt` files themselves. Per the pipeline doc, they live in Google Drive at `/content/drive/MyDrive/BSE_Transcripts_Text/`, organized as one folder per company, processed in Google Colab. The two CSVs here are the *only* local artifacts — everything upstream (scraping/collecting transcripts) already happened elsewhere.

## 3. How Each Output Was Produced

### 3a. `ClimateBert_Scores_Output_Updated.csv` — via ClimateBERT
- Base method: [2110.12010v3ClimateBert.pdf](2110.12010v3ClimateBert.pdf) — DistilRoBERTa further pretrained on 2M+ climate paragraphs (news/abstracts/corporate reports), then fine-tuned for (a) climate-relevance classification and (b) risk/opportunity/neutral sentiment.
- Applied to each transcript: split into sentences → each sentence classified as climate-related or not → climate sentences further classified as risk/opportunity/neutral.
- `Climate_Exposure_Score` = `Climate_Sentences_Count / Total_Sentences * 100` (**verified exactly** against the data).
- `Sentiment_Risk_Count + Sentiment_Opportunity_Count + Sentiment_Neutral_Count == Climate_Sentences_Count` (**verified exactly** — these three always sum to the climate sentence count).

### 3b. `merged_quarterly_transcripts_results_new.csv` — via Loughran-McDonald + FinBERT
Documented step-by-step in `tone explanation sectionwise.pdf`. Pipeline:
1. Mount Google Drive, iterate every company folder, every `.txt` transcript.
2. Download the **Loughran-McDonald Master Dictionary** — a finance-specific sentiment lexicon (chosen because generic lexicons misclassify finance words, e.g. "liability" is negative in finance but neutral elsewhere).
3. Parse `Year`/`Quarter` out of the filename (two supported patterns: `YYYY_QN` or `QN_YYYY`; filenames that match neither become `Quarter="Unknown"`).
4. Clean text (strip numbers/punctuation, lowercase) → tokenize into sentences and words (NLTK).
5. Count words falling into LM's **Positive / Negative / Uncertain / Weak Modal** categories.
6. `Tone_Score = (Positive_Count - Negative_Count) / (Positive_Count + Negative_Count + 1e-10)` → range -1 (very negative) to +1 (very positive).
7. `Percent_Uncertain`, `Percent_Weak_Modal` = category count / total words × 100 (hedging/ambiguity signals).
8. Readability: `Fog_Index = 0.4 × (avg words/sentence + % complex words[≥3 syllables])` (Gunning Fog — 12≈high school, 16≈college, 18+≈graduate). `File_Size_Readability = -log(File_Size_MB + 1)` as a verbosity proxy.
9. **FinBERT** (a separate pretrained finance sentiment model) is also run on the same text, giving `FinBERT_Positive/Negative/Neutral` probabilities and a derived `FinBERT_Tone` — a second, model-based (vs. dictionary-based) sentiment read for comparison.
10. Results saved incrementally (checkpoint every 1,000 files) and exported to a multi-sheet Excel workbook (raw data, descriptive stats, quarterly/yearly aggregates, company rankings, correlation matrix, summary insights) — `merged_quarterly_transcripts_results_new.csv` is the flattened "Raw_Data" sheet.

**Known documented limitations** (from the pipeline doc itself): dictionary approach lacks context; no separation of CEO vs CFO speech; no comparison against actual reported financials; filename parsing is fragile (source of the `Unknown`/`.error` rows below).

## 4. Data Dictionary

### `ClimateBert_Scores_Output_Updated.csv` (15,812 rows × 12 cols)

| Column | Type | Meaning |
|---|---|---|
| `Filename` | string | Source transcript file, e.g. `534139_2025_Q4.txt`. **Join key.** |
| `Security_Code` | int | BSE scrip/security code for the company. |
| `Company_Name` | string | Full legal company name. |
| `NSE_Name` | string | Short ticker-style name (NSE). |
| `Year` | int | Fiscal year of the call, parsed from filename. |
| `Quarter` | string | `Q1`–`Q4`, or `Unknown` (20 rows), or `Q#.error` (9 rows — filename parse failure). |
| `Total_Sentences` | int | Sentences in the transcript. |
| `Climate_Sentences_Count` | int | Sentences classified as climate-related. |
| `Climate_Exposure_Score` | float | `Climate_Sentences_Count / Total_Sentences × 100`. |
| `Sentiment_Risk_Count` | int | Climate sentences classified as *risk*. |
| `Sentiment_Opportunity_Count` | int | Climate sentences classified as *opportunity*. |
| `Sentiment_Neutral_Count` | int | Climate sentences classified as *neutral*. |

### `merged_quarterly_transcripts_results_new.csv` (15,828 rows × 20 cols)

| Column | Type | Meaning |
|---|---|---|
| `Company_ID` | int | BSE scrip code — same scheme as `Security_Code` above. |
| `Company_Name` | string | Full legal company name. |
| `Year` / `Quarter` | int / string | Same parsing logic as above (`Unknown` for 20 rows; no `.error` rows here — this script's parser is more permissive). |
| `File_Name` | string | Source transcript file. **Join key**, matches `Filename` above. |
| `Positive_Count` / `Negative_Count` | int | Loughran-McDonald positive/negative word counts. |
| `Uncertain_Count` / `Weak_Modal_Count` | int | LM uncertainty/hedging word counts. |
| `Tone_Score` | float | `(Pos-Neg)/(Pos+Neg+ε)`, range ≈ -1 to +1. |
| `Percent_Uncertain` / `Percent_Weak_Modal` | float | Category count / total words × 100. |
| `Total_Words` | int | Word count after cleaning. |
| `File_Size_MB` | float | Raw transcript file size. |
| `File_Size_Readability` | float | `-log(File_Size_MB + 1)`, verbosity proxy. |
| `Fog_Index` | float | Gunning Fog readability score. |
| `FinBERT_Positive/Negative/Neutral` | float | FinBERT model's class probabilities. |
| `FinBERT_Tone` | float | Derived net FinBERT sentiment (null for 16 rows — see §5). |

## 5. Data Relationships & Known Issues

- **Primary join key:** `Filename` (ClimateBERT file) = `File_Name` (merged file). All 15,812 ClimateBERT rows have an exact match in the merged file. **Filename pattern:** `{Security_Code}_{Year}_{Quarter}[_{n}].txt`.
- **Secondary key:** `Security_Code` = `Company_ID` (both BSE codes). 1,362 of 1,363 company codes overlap between the two files — near-total, not 100%.
- **Grain:** nominally one row per company + year + quarter, but **not unique** — ~500 company-quarters have 2+ rows because of filenames with odd-numbered suffixes (`_1`, `_3`, `_5`, `_7`, `_9` — never even numbers, cause not yet confirmed, possibly split prepared-remarks vs Q&A segments or duplicate uploads). **Needs a decision before aggregating by company-quarter** — candidates: sum, average, or keep as separate sub-rows. Flagged as open in §6.
- **16 extra rows** exist in the merged CSV with no ClimateBERT counterpart, and these are exactly the 16 rows where `FinBERT_Tone` is null — suggesting the same 16 source files had a text-extraction problem that broke both the ClimateBERT step and the FinBERT step.
- **Data quality to clean before charting:**
  - 2 rows in the ClimateBERT file have impossible `Year` values (2613, 2525) — both `Quarter="Unknown"`, filename parse artifacts.
  - The merged file has ~20 similarly garbled `Year` values on its `Unknown`-quarter rows (e.g. 5031, 5061) — same root cause, different corruption.
  - 9 rows in the ClimateBERT file carry `Quarter="Q#.error"` — the merged file parsed the *same filenames* correctly as clean `Q1`–`Q4`, meaning its parser is the more reliable one to trust for quarter values.
  - Recommendation: build a single cleaned `Year`/`Quarter` field (prefer the merged file's parse), and exclude/flag the ~22 truly unparseable rows rather than dropping them silently.

## 6. Decisions Made

1. **Dashboard platform: Custom coded web app** (not a Claude Artifact, not a BI tool) — we own the full codebase.
2. **Stack: Streamlit (Python)** — chosen for fastest iteration on a pandas-heavy exploration dashboard, matches the existing Python/Colab pipeline skillset, free-tier deployable via Streamlit Community Cloud.
3. **Duplicate company-quarter rows** (`_1`/`_3`/`_5` suffix files) — **still open**. No local Google Drive sync found on this machine, so the raw transcript pairs can't be inspected directly from here. Two ways to unblock: (a) user drops 2-3 example pairs into this folder (e.g. `500038_2024_Q4_1.txt` + `500038_2024_Q4_3.txt`), or (b) user checks Drive and reports back what the suffixes represent. **Interim default: sum raw counts and recompute derived scores** so the cleaning script isn't blocked — revisit once confirmed.
4. **Data cleaning ownership: one-time Python script** → canonical cleaned CSV, which the Streamlit app just reads (not live cleaning inside the app).
5. **Not currently a git repo** — will `git init` this folder as part of setting up the app project structure (standard for a deployable codebase), unless told otherwise.

## 7. Proposed Workflow

1. **Clean & merge** — join the two CSVs on `Filename`, resolve duplicate company-quarters (sum, pending confirmation), fix Year/Quarter, produce one canonical dataset (`data/clean_transcripts.csv` or similar).
2. **Aggregate views** — precompute company-level, quarter-level, and year-level summaries (mirrors the "Statistical Analysis" step already done in the LM pipeline: descriptive stats, quarterly/yearly aggregates, top/bottom performers, correlations).
3. **Build the Streamlit app** — company search/filter, trend charts (climate exposure & tone over time), rankings, correlation views (e.g. does higher climate exposure correlate with tone or uncertainty?).
4. **Deploy** — Streamlit Community Cloud (free, needs a GitHub repo to connect) or user's own hosting preference.

## 8. Progress Log

- **2026-09-16** — Explored both CSVs in depth: confirmed schemas, verified `Climate_Exposure_Score` and sentiment-count-sum formulas exactly match the data, established `Filename`/`File_Name` as the reliable join key, found and documented the duplicate-company-quarter issue (~500 cases) and the Year/Quarter parsing defects (~30 rows total across both files). Read the ClimateBERT paper in full and the tone-analysis pipeline doc in full. Created this log.
- **2026-09-16** — Decided: custom Streamlit app (not Artifact/BI tool), one-time cleaning script → canonical CSV → app reads clean data, will git-init the folder. Duplicate-row handling still pending (no local Drive access to investigate `_1`/`_3` suffixes — using "sum" as interim default). Next: draft an implementation plan for the cleaning script + app structure before writing code.
- **2026-09-22/23** — Approved implementation plan (saved at `~/.claude/plans/radiant-tickling-mountain.md`). Set up project structure (`app/`, `data/raw/`, `scripts/`, `tests/`), created a Python virtual environment (`.venv`) with streamlit/pandas/plotly/pytest/reportlab. Moved the two raw CSVs into `data/raw/`. Built and ran `scripts/clean_data.py`: merges both raw files on `Filename`/`File_Name`, reconciles Year/Quarter (preferring the tone file's parse), resolves duplicate company-quarters via the interim sum-and-recompute policy, recomputes exact ratio columns, and weighted-averages FinBERT/Fog_Index for combined rows. Output: `data/clean_transcripts.csv`, 15,329 rows × 32 columns (from 15,828 source rows; 428 rows are combined multi-file groups; 20 rows flagged `parse_ok=False`; 15 rows have no climate score). All 5 invariant tests in `tests/test_clean_data.py` pass. Spot-verified edge cases directly against the data: company `533287` (zero climate-scored transcripts across all 8 of its quarters) and `543974_2025_Q4` (a mixed-coverage duplicate group — one real file, one extraction-failure file) both resolve correctly. Started `app/lib/` (only `constants.py` written so far — page files not yet built, paused to realign on explaining the workflow first).
- **2026-09-27** — Verified `FinBERT_Tone = FinBERT_Positive − FinBERT_Negative` empirically (matches to rounding across the dataset) and used it in documentation rather than guessing. Built `scripts/generate_process_doc.py` (using reportlab) to produce `Process_Documentation.pdf` at the project root — a 15-page report covering both raw datasets column-by-column, the 7-step cleaning pipeline, the canonical clean schema, a full column-to-dashboard mapping, and the dashboard's 5 planned pages. All figures in the PDF are computed live from the actual data rather than hand-typed. Authored to Prathviraj Singh.
- **2026-09-27** — Built the Streamlit app in full: `app/lib/data.py` (cached load + period/filter/aggregation helpers), `app/lib/charts.py` (Plotly figure builders), and all 5 pages (`Home`, `Company_Explorer`, `Rankings`, `Correlations`, `About_Data`), plus `requirements.txt`, `.gitignore`, `README.md`. Verified every page headlessly via `streamlit.testing.v1.AppTest` (rooted at `Home.py` with `switch_page`, matching real runtime behavior rather than testing page files in isolation) — no exceptions on any page. Replaced the deprecated `use_container_width` argument with `width="stretch"` across all files (Streamlit's own warning showed it was already past its stated removal date in the installed version). While exercising the known edge cases (company `533287`, zero climate data), **found and fixed a real bug**: `Tone_Score`'s formula `(Pos-Neg)/(Pos+Neg+1e-10)` had no zero-guard (unlike the other ratio columns), so the 15 zero-word extraction-failure rows were resolving to a misleading `0.0` ("looks like real neutral sentiment") instead of `NaN`. Fixed in `scripts/clean_data.py` to use the same `safe_div` guard as the other ratios, re-ran the cleaning pipeline and all 5 tests (still pass), and re-verified via AppTest that the affected company now correctly shows "No data available" instead of a fake flat-line chart. App runs locally at `http://localhost:8501` (`streamlit run app/Home.py`). **Not yet done:** git init/commit and GitHub/Streamlit Cloud deployment (Section 7 deployment steps) — still local-only. Duplicate-suffix meaning (`_1/_3/_5`) still unconfirmed, sum-and-recompute remains the interim policy.
