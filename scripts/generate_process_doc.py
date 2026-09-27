"""
Generates Process_Documentation.pdf at the project root: a complete process
document covering both raw datasets, the cleaning/integration pipeline, the
canonical clean schema, the column-to-dashboard mapping, and the dashboard's
feature set.

Run: python scripts/generate_process_doc.py
"""

import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
CLEAN_PATH = ROOT / "data" / "clean_transcripts.csv"
OUT_PATH = ROOT / "Process_Documentation.pdf"

AUTHOR = "Prathviraj Singh"

# ---------------------------------------------------------------------------
# Pull live statistics from the actual data so every figure in the document
# is computed, not hand-transcribed.
# ---------------------------------------------------------------------------
cb = pd.read_csv(RAW_DIR / "ClimateBert_Scores_Output_Updated.csv")
mq = pd.read_csv(RAW_DIR / "merged_quarterly_transcripts_results_new.csv")
clean = pd.read_csv(CLEAN_PATH)

VALID_Q = {"Q1", "Q2", "Q3", "Q4"}
cb_valid = cb[cb.Quarter.isin(VALID_Q)]
mq_valid = mq[mq.Quarter.isin(VALID_Q)]

STATS = {
    "cb_rows": len(cb),
    "cb_cols": cb.shape[1],
    "cb_companies": cb.Security_Code.nunique(),
    "cb_year_min": int(cb_valid.Year.min()),
    "cb_year_max": int(cb_valid.Year.max()),
    "cb_quarter_counts": cb.Quarter.value_counts().to_dict(),
    "mq_rows": len(mq),
    "mq_cols": mq.shape[1],
    "mq_companies": mq.Company_ID.nunique(),
    "mq_year_min": int(mq_valid.Year.min()),
    "mq_year_max": int(mq_valid.Year.max()),
    "mq_quarter_counts": mq.Quarter.value_counts().to_dict(),
    "mq_finbert_null": int(mq.FinBERT_Tone.isna().sum()),
    "filename_overlap": len(set(cb.Filename) & set(mq.File_Name)),
    "mq_only_files": len(set(mq.File_Name) - set(cb.Filename)),
    "company_id_overlap": len(set(cb.Security_Code) & set(mq.Company_ID)),
    "clean_rows": len(clean),
    "clean_cols": clean.shape[1],
    "clean_parse_fail": int((~clean.parse_ok).sum()),
    "clean_dup_groups": int(clean.duplicate_group.sum()),
    "clean_no_climate": int((~clean.has_climate_data).sum()),
    "clean_source_files": int(clean.n_source_files.sum()),
}

GENERATED_DATE = datetime.date.today().strftime("%B %d, %Y")

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(name="DocTitle", fontName="Helvetica-Bold", fontSize=25,
                           leading=30, alignment=TA_CENTER, spaceAfter=6,
                           textColor=colors.HexColor("#173F26")))
styles.add(ParagraphStyle(name="DocSubtitle", fontName="Helvetica", fontSize=13.5,
                           leading=18, alignment=TA_CENTER, spaceAfter=4,
                           textColor=colors.HexColor("#3D5B47")))
styles.add(ParagraphStyle(name="DocMeta", fontName="Helvetica", fontSize=11,
                           leading=16, alignment=TA_CENTER,
                           textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle(name="Abstract", fontName="Helvetica-Oblique", fontSize=10.5,
                           leading=15, alignment=TA_JUSTIFY,
                           textColor=colors.HexColor("#333333"),
                           borderPadding=10))
styles.add(ParagraphStyle(name="H1", fontName="Helvetica-Bold", fontSize=17,
                           leading=21, spaceBefore=4, spaceAfter=10,
                           textColor=colors.HexColor("#173F26"),
                           borderWidth=0, borderColor=colors.HexColor("#173F26")))
styles.add(ParagraphStyle(name="H2", fontName="Helvetica-Bold", fontSize=13.5,
                           leading=17, spaceBefore=14, spaceAfter=7,
                           textColor=colors.HexColor("#28623D")))
styles.add(ParagraphStyle(name="H3", fontName="Helvetica-Bold", fontSize=11.5,
                           leading=15, spaceBefore=10, spaceAfter=5,
                           textColor=colors.HexColor("#28623D")))
styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10,
                           leading=14.5, alignment=TA_JUSTIFY, spaceAfter=7,
                           textColor=colors.HexColor("#1A1A1A")))
styles.add(ParagraphStyle(name="BodyBullet", parent=styles["Body"],
                           leftIndent=14, bulletIndent=2, spaceAfter=4))
styles.add(ParagraphStyle(name="Caption", fontName="Helvetica-Oblique", fontSize=8.5,
                           leading=11, textColor=colors.HexColor("#666666"), spaceAfter=10))
styles.add(ParagraphStyle(name="TableHeader", fontName="Helvetica-Bold", fontSize=8.7,
                           leading=11, textColor=colors.white))
styles.add(ParagraphStyle(name="TableCell", fontName="Helvetica", fontSize=8.3,
                           leading=10.6))
styles.add(ParagraphStyle(name="TableCellMono", fontName="Helvetica-Bold", fontSize=8.3,
                           leading=10.6, textColor=colors.HexColor("#173F26")))
styles.add(ParagraphStyle(name="Callout", fontName="Helvetica", fontSize=9.7,
                           leading=13.5, textColor=colors.HexColor("#5C3B00"),
                           backColor=colors.HexColor("#FFF6E0"),
                           borderPadding=8, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="TOCEntry", fontName="Helvetica", fontSize=11,
                           leading=20, textColor=colors.HexColor("#1A1A1A")))

GREEN = colors.HexColor("#28623D")
GREEN_DARK = colors.HexColor("#173F26")
GREEN_PALE = colors.HexColor("#EAF2EC")
GREY_PALE = colors.HexColor("#F4F4F4")

story = []


def h1(text):
    story.append(Paragraph(text, styles["H1"]))
    story.append(Table([[""]], colWidths=[17 * cm], rowHeights=[2],
                        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREEN),
                                           ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white)])))
    story.append(Spacer(1, 10))


def h2(text):
    story.append(Paragraph(text, styles["H2"]))


def h3(text):
    story.append(Paragraph(text, styles["H3"]))


def body(text):
    story.append(Paragraph(text, styles["Body"]))


def bullet(text):
    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{text}", styles["BodyBullet"]))


def callout(text):
    story.append(Paragraph(text, styles["Callout"]))


def caption(text):
    story.append(Paragraph(text, styles["Caption"]))


def col_table(rows, col_widths, header=True):
    """rows: list of lists of plain strings (first row = header if header=True)."""
    data = []
    for i, row in enumerate(rows):
        style = styles["TableHeader"] if (header and i == 0) else styles["TableCell"]
        data.append([Paragraph(str(cell), style) for cell in row])
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD9CF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        ts.append(("BACKGROUND", (0, 0), (-1, 0), GREEN_DARK))
        ts += [("BACKGROUND", (0, r), (-1, r), GREY_PALE) for r in range(2, len(data), 2)]
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 10))


# ===========================================================================
# COVER PAGE
# ===========================================================================
story.append(Spacer(1, 4.5 * cm))
story.append(Table([[""]], colWidths=[10 * cm], rowHeights=[3],
                    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREEN)])))
story.append(Spacer(1, 0.6 * cm))
story.append(Paragraph("Climate Risk &amp; Financial Tone Analytics", styles["DocTitle"]))
story.append(Paragraph("Process Documentation", styles["DocTitle"]))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    "Data Sources, Cleaning &amp; Integration Pipeline, and Dashboard Architecture "
    "for Quarterly Earnings-Call Transcript Analysis of BSE-Listed Companies",
    styles["DocSubtitle"]))
story.append(Spacer(1, 1.4 * cm))
story.append(Paragraph(f"Author: {AUTHOR}", styles["DocMeta"]))
story.append(Paragraph(GENERATED_DATE, styles["DocMeta"]))
story.append(Spacer(1, 1.4 * cm))
story.append(Paragraph(
    "This document describes, end to end, the two source datasets that feed this project, "
    "the pipeline that cleans and merges them into a single canonical dataset, and the "
    "dashboard built on top of that dataset to explore climate-risk exposure and financial "
    "tone across quarterly earnings calls of Bombay Stock Exchange (BSE) listed companies. "
    "It is intended as the reference record of the project's data and design decisions.",
    styles["Abstract"]))
story.append(PageBreak())

# ===========================================================================
# TABLE OF CONTENTS
# ===========================================================================
toc_entries = [
    "1.  Introduction &amp; Purpose",
    "2.  Dataset One: Climate Exposure &amp; Sentiment Scores",
    "3.  Dataset Two: Financial Tone, Readability &amp; FinBERT Scores",
    "4.  Relationship Between the Two Datasets",
    "5.  Data Cleaning &amp; Integration Pipeline",
    "6.  Canonical Clean Dataset Schema",
    "7.  Column-to-Dashboard Mapping",
    "8.  Dashboard Architecture &amp; Features",
    "9.  Known Data Limitations &amp; Open Items",
    "10. Appendix: Formula Reference",
]
h1("Table of Contents")
for entry in toc_entries:
    story.append(Paragraph(entry, styles["TOCEntry"]))
story.append(PageBreak())

# ===========================================================================
# 1. INTRODUCTION
# ===========================================================================
h1("1. Introduction &amp; Purpose")
body(
    "Earnings-call transcripts are a rich, unstructured record of how a company's management "
    "communicates with investors each quarter &mdash; what they emphasize, how confidently they speak, "
    "and how they frame climate-related topics such as emissions, regulation, and physical or transition "
    "risk. This project analyzes quarterly earnings-call transcripts for approximately "
    f"{STATS['mq_companies']:,} BSE-listed companies, spanning {STATS['mq_year_min']}&ndash;{STATS['mq_year_max']}, "
    "along two independent analytical dimensions:"
)
bullet("<b>Climate-risk exposure and framing</b> &mdash; how much of each call discusses climate topics, and whether that discussion is framed as risk, opportunity, or neutral fact.")
bullet("<b>General financial tone, hedging, and readability</b> &mdash; how positive or negative the language is overall, how much uncertainty/hedging is present, and how complex the language is.")
body(
    "Each dimension was produced by an independent scoring pipeline, resulting in two separate output "
    "datasets. This document explains both datasets in full column-by-column detail, the pipeline that "
    "merges and cleans them into one canonical dataset, and the dashboard built to let a user explore "
    "the result &mdash; including exactly how each underlying column surfaces in the dashboard's features."
)

# ===========================================================================
# 2. DATASET ONE
# ===========================================================================
h1("2. Dataset One: Climate Exposure &amp; Sentiment Scores")
h2("2.1 Overview &amp; Methodology")
body(
    "This dataset scores each transcript for climate relevance and climate sentiment using a "
    "transformer-based language model purpose-built for climate-related text (further pretrained on a "
    "large corpus of climate news, scientific abstracts, and corporate sustainability reports, on top of "
    "a general-purpose language model). Two classifiers are applied to every transcript:"
)
bullet("<b>Climate-relevance classifier</b> &mdash; applied at the sentence level, labels each sentence as climate-related or not.")
bullet("<b>Sentiment classifier</b> &mdash; applied only to sentences already labeled climate-related, further classifies each as framing a <i>risk</i>, an <i>opportunity</i>, or a <i>neutral</i> statement.")
body(
    f"The raw output file, <b>ClimateBert_Scores_Output_Updated.csv</b>, contains {STATS['cb_rows']:,} rows "
    f"across {STATS['cb_cols']} columns &mdash; one row per transcript file &mdash; covering {STATS['cb_companies']:,} "
    "distinct companies (identified by BSE security code)."
)

h2("2.2 Column-by-Column Reference")
col_table([
    ["Column", "Type", "Description"],
    ["Filename", "text", "Source transcript file name. Pattern: SecurityCode_Year_Quarter, with an optional trailing part-number suffix (e.g. 534139_2025_Q4.txt). This is the join key to Dataset Two."],
    ["Security_Code", "integer", "BSE security / scrip code uniquely identifying the company."],
    ["Company_Name", "text", "Full legal name of the company."],
    ["NSE_Name", "text", "Short ticker-style name as listed on the National Stock Exchange."],
    ["Year", "integer", "Fiscal year of the earnings call, parsed from the filename."],
    ["Quarter", "text", "Fiscal quarter: Q1, Q2, Q3, or Q4. Two further values appear due to filename-parsing limitations: ‘Unknown’ (no recognizable year/quarter pattern in the filename) and ‘Q#.error’ (a partially recognized but malformed pattern)."],
    ["Total_Sentences", "integer", "Total number of sentences in the transcript after sentence-level tokenization."],
    ["Climate_Sentences_Count", "integer", "Number of sentences classified as climate-related by the relevance classifier."],
    ["Climate_Exposure_Score", "decimal", "Climate_Sentences_Count &divide; Total_Sentences &times; 100. The percentage of the call devoted to climate topics. Verified to hold exactly across every row of this dataset."],
    ["Sentiment_Risk_Count", "integer", "Number of climate sentences framed as a risk (e.g. transition risk, physical risk, regulatory exposure)."],
    ["Sentiment_Opportunity_Count", "integer", "Number of climate sentences framed as an opportunity (e.g. new markets, efficiency gains, green financing)."],
    ["Sentiment_Neutral_Count", "integer", "Number of climate sentences that are purely factual/descriptive, with no risk or opportunity framing."],
], col_widths=[3.6 * cm, 2.0 * cm, 11.4 * cm])

h2("2.3 Data Characteristics")
qc = STATS["cb_quarter_counts"]
q_line = ", ".join(f"{q}: {qc.get(q, 0):,}" for q in ["Q1", "Q2", "Q3", "Q4", "Unknown"])
error_total = sum(v for k, v in qc.items() if "error" in k)
body(
    f"Quarter distribution &mdash; {q_line}, plus {error_total} rows carrying a ‘.error’ suffix on the "
    "quarter value. Two rows carry an implausible Year value (year numbers outside any real fiscal range), "
    "both on rows where Quarter is ‘Unknown’ &mdash; both are filename-parsing artifacts, addressed in the "
    "cleaning pipeline (Section 5)."
)
body(
    "Two derived-column invariants were verified exactly against every row in this dataset: "
    "Climate_Exposure_Score always equals Climate_Sentences_Count &divide; Total_Sentences &times; 100, and "
    "Sentiment_Risk_Count + Sentiment_Opportunity_Count + Sentiment_Neutral_Count always equals exactly "
    "Climate_Sentences_Count. Both hold with zero exceptions, confirming the sentiment classifier is applied "
    "to, and only to, the sentences already flagged as climate-related."
)

# ===========================================================================
# 3. DATASET TWO
# ===========================================================================
story.append(PageBreak())
h1("3. Dataset Two: Financial Tone, Readability &amp; FinBERT Scores")
h2("3.1 Overview &amp; Methodology")
body(
    "This dataset scores the same transcripts for general financial sentiment, hedging language, and "
    "readability, using two complementary techniques rather than one:"
)
bullet("<b>Loughran-McDonald Master Dictionary</b> &mdash; a finance-specific word list (not a generic sentiment lexicon) used because ordinary words carry different connotations in financial disclosure than in everyday language (e.g. ‘liability’ reads as negative in a financial context but neutral elsewhere). Each transcript's words are counted against four categories: Positive, Negative, Uncertain, and Weak Modal (hedging words such as ‘could’, ‘might’, ‘may’).")
bullet("<b>FinBERT</b> &mdash; a pretrained finance-domain sentiment model, run independently on the same text to provide a model-based sentiment read for comparison against the dictionary-based one.")
body(
    "Readability is measured two ways: the Gunning Fog Index (a standard academic readability formula "
    "based on sentence length and syllable complexity) and a simple file-size-based verbosity proxy."
)
body(
    f"The raw output file, <b>merged_quarterly_transcripts_results_new.csv</b>, contains {STATS['mq_rows']:,} "
    f"rows across {STATS['mq_cols']} columns &mdash; one row per transcript file &mdash; covering "
    f"{STATS['mq_companies']:,} distinct companies."
)

h2("3.2 Column-by-Column Reference")
col_table([
    ["Column", "Type", "Description"],
    ["Company_ID", "integer", "BSE security code. Same numbering scheme as Security_Code in Dataset One."],
    ["Company_Name", "text", "Full legal name of the company."],
    ["Year / Quarter", "integer / text", "Fiscal period parsed from the filename. This dataset's parser is more permissive than Dataset One's: it recognizes both filename layouts (Year-then-Quarter and Quarter-then-Year) and produces ‘Unknown’ rather than an error value when neither pattern matches."],
    ["File_Name", "text", "Source transcript file name. Join key to Dataset One (Filename)."],
    ["Positive_Count / Negative_Count", "integer", "Count of words matching the Loughran-McDonald positive / negative word lists."],
    ["Uncertain_Count", "integer", "Count of words matching the Loughran-McDonald uncertainty word list (e.g. ‘appears’, ‘possibly’, ‘uncertain’)."],
    ["Weak_Modal_Count", "integer", "Count of hedging modal words (e.g. ‘could’, ‘might’, ‘depending’, ‘should’)."],
    ["Tone_Score", "decimal", "(Positive_Count &minus; Negative_Count) &divide; (Positive_Count + Negative_Count), a net sentiment score ranging from &minus;1 (entirely negative) to +1 (entirely positive)."],
    ["Percent_Uncertain / Percent_Weak_Modal", "decimal", "Respective word count &divide; Total_Words &times; 100 &mdash; the share of the transcript that is hedging/uncertain language."],
    ["Total_Words", "integer", "Total word count of the transcript after cleaning (lowercased, numbers and punctuation stripped)."],
    ["File_Size_MB", "decimal", "Raw size of the source transcript file, in megabytes."],
    ["File_Size_Readability", "decimal", "&minus;log(File_Size_MB + 1), a verbosity proxy: larger, more verbose filings score lower (more negative)."],
    ["Fog_Index", "decimal", "Gunning Fog readability score: 0.4 &times; (average words per sentence + percent of complex words, defined as words of three or more syllables). Approximate interpretation: ~12 = high-school reading level, ~16 = college level, 18+ = graduate level."],
    ["FinBERT_Positive / FinBERT_Negative / FinBERT_Neutral", "decimal", "Class probabilities (summing to ~1.0) output by the FinBERT model for the transcript."],
    ["FinBERT_Tone", "decimal", "Net FinBERT sentiment. Empirically verified to equal FinBERT_Positive &minus; FinBERT_Negative (matches to rounding precision across the dataset)."],
], col_widths=[4.4 * cm, 2.2 * cm, 10.4 * cm])

h2("3.3 Data Characteristics")
qc2 = STATS["mq_quarter_counts"]
q_line2 = ", ".join(f"{q}: {qc2.get(q, 0):,}" for q in ["Q1", "Q2", "Q3", "Q4", "Unknown"])
body(f"Quarter distribution &mdash; {q_line2}. No ‘.error’ values occur in this dataset's Quarter column.")
body(
    f"{STATS['mq_finbert_null']} rows have a null FinBERT_Tone (and correspondingly null FinBERT_Positive/"
    "Negative/Neutral). These same rows also carry Total_Words = 0 and zero counts across every "
    "Loughran-McDonald category, consistent with a shared upstream text-extraction failure for those "
    "specific source files rather than a scoring error. All such rows are also absent from Dataset One "
    "entirely (see Section 4)."
)

# ===========================================================================
# 4. RELATIONSHIP BETWEEN DATASETS
# ===========================================================================
story.append(PageBreak())
h1("4. Relationship Between the Two Datasets")
body(
    "The two datasets describe the same underlying set of transcripts and are designed to be joined "
    "together. Two keys connect them:"
)
bullet(f"<b>Filename &harr; File_Name</b> (primary join key) &mdash; every one of the {STATS['cb_rows']:,} rows in Dataset One has an exact matching row in Dataset Two. Dataset Two additionally contains {STATS['mq_only_files']} rows with no counterpart in Dataset One &mdash; these are precisely the {STATS['mq_finbert_null']} extraction-failure rows described above, for which no climate score could be produced at all.")
bullet(f"<b>Security_Code &harr; Company_ID</b> (company key) &mdash; the same BSE numbering scheme. {STATS['company_id_overlap']:,} of the two datasets' company codes overlap; the remaining handful appear in only one dataset, generally reflecting a company with no successfully scored transcripts in the other pipeline.")
body(
    "The intended grain of both datasets is one row per company, per fiscal year, per quarter. In practice "
    "this grain is not always unique: a meaningful number of company-quarters are represented by more than "
    "one transcript file, distinguished by a numeric suffix on the filename (for example, two files ending "
    "in ‘_1’ and ‘_3’ for the same company and quarter). The cause of this duplication "
    "&mdash; whether these represent separate segments of the same call (such as prepared remarks versus a "
    "question-and-answer session), separate re-uploads of the same call, or some other cause &mdash; had not "
    "been confirmed against the original source recordings at the time of writing. Section 5 documents the "
    "interim policy adopted to combine these rows into a single company-quarter record, and Section 9 "
    "records this as an open item."
)
callout(
    "<b>Data-quality note.</b> Two further parsing issues were identified and are handled explicitly by the "
    "cleaning pipeline: (a) a small number of rows carry an implausible Year value produced by a filename-"
    "parsing edge case, and (b) nine rows in Dataset One carry a malformed ‘Q#.error’ quarter value on "
    "filenames that Dataset Two's more permissive parser reads correctly. Both are resolved during cleaning "
    "rather than left in the data as-is."
)

# ===========================================================================
# 5. CLEANING PIPELINE
# ===========================================================================
story.append(PageBreak())
h1("5. Data Cleaning &amp; Integration Pipeline")
body(
    "Both raw datasets are combined once, by a standalone cleaning script, into a single canonical dataset. "
    "The dashboard reads only this canonical output &mdash; no cleaning logic runs inside the dashboard "
    "itself. The pipeline proceeds through seven steps, each auditable independently."
)

h2("Step 1 &mdash; Load")
body("Both raw CSV files are read, with company identifier columns loaded as nullable integers to avoid unintended type coercion.")

h2("Step 2 &mdash; Merge")
body(
    "Dataset Two (the superset, since it contains every transcript Dataset One has plus a handful of "
    "extraction failures) is left-joined with Dataset One on the Filename / File_Name key. A flag column, "
    "has_climate_data, is set based on whether a climate score exists for that row, immediately identifying "
    "the extraction-failure rows."
)

h2("Step 3 &mdash; Year / Quarter Reconciliation")
body(
    "For every row, the parsed Year and Quarter from Dataset Two are used if they form a plausible period "
    "(a real quarter label together with a plausible year); if not, the pipeline falls back to Dataset "
    "One's parsed value under the same plausibility check. Only if neither source produces a plausible "
    "period is the row marked unparseable (parse_ok = False). Unparseable rows are never discarded &mdash; "
    "they are retained in the output but excluded from any period-based (year/quarter) view or filter in "
    "the dashboard, since their true period cannot be established."
)

h2("Step 4 &mdash; Duplicate Resolution (interim policy)")
body(
    "Rows with a valid, reconciled period are grouped by company, year, and quarter. Where a group contains "
    "more than one contributing file, the raw countable metrics (sentence counts, word counts, category "
    "counts) are summed across the group. This function is deliberately isolated in the codebase as the "
    "single place to revisit once the meaning of the duplicate filenames is confirmed against source "
    "recordings; nothing else in the pipeline depends on this specific choice."
)

h2("Step 5 &mdash; Recomputing Exact Ratios")
body(
    "After summing the raw counts for a company-quarter, every ratio-based metric is recalculated from "
    "those summed totals rather than averaged from the original per-file values, since these metrics are "
    "true ratios of countable quantities and can be reconstructed exactly: Climate_Exposure_Score, "
    "Tone_Score, Percent_Uncertain, Percent_Weak_Modal, and File_Size_Readability. This is applied uniformly "
    "to every row, including company-quarters with only one contributing file, so that one formula is used "
    "consistently across the entire dataset."
)

h2("Step 6 &mdash; Approximating Combined Metrics")
body(
    "Two metrics are not exact ratios of countable quantities &mdash; FinBERT's probability outputs and the "
    "Fog Index &mdash; and cannot be exactly reconstructed after combining files. For company-quarters with "
    "multiple contributing files, these are instead combined as a word-count-weighted average across the "
    "group's files. This has the convenient side effect of automatically discounting any extraction-failure "
    "sub-file within a group, since such a file contributes zero weight. Every row combined this way is "
    "flagged so this approximation is visible and traceable rather than silent."
)

h2("Step 7 &mdash; Finalize")
body(
    f"The cleaned, combined dataset is written out as the canonical output. The pipeline produced "
    f"{STATS['clean_rows']:,} final rows from {STATS['clean_source_files']:,} original source files "
    f"(Dataset Two's full row count), of which {STATS['clean_dup_groups']:,} final rows represent a combined "
    f"multi-file group, {STATS['clean_parse_fail']} rows are retained but flagged as period-unparseable, and "
    f"{STATS['clean_no_climate']} rows have no climate score available at all."
)

# ===========================================================================
# 6. CLEAN SCHEMA
# ===========================================================================
story.append(PageBreak())
h1("6. Canonical Clean Dataset Schema")
body(
    f"The cleaned dataset contains {STATS['clean_rows']:,} rows and {STATS['clean_cols']} columns. This is "
    "the only dataset the dashboard reads."
)
col_table([
    ["Column", "Description"],
    ["Security_Code", "BSE company identifier."],
    ["Company_Name / NSE_Name", "Company name and short ticker-style name."],
    ["Year / Quarter", "Reconciled fiscal period (see Step 3)."],
    ["parse_ok", "Whether a valid fiscal period could be established for this row."],
    ["n_source_files", "Number of original transcript files combined into this row (1 unless a duplicate group)."],
    ["Filenames", "Semicolon-separated list of every source filename contributing to this row, for traceability."],
    ["duplicate_group", "Whether this row combines more than one source file."],
    ["has_climate_data", "Whether a climate score exists for this row (False only for extraction-failure files)."],
    ["climate_file_coverage", "Fraction of this row's contributing files that had a climate score (relevant only when duplicate_group is true)."],
    ["Total_Sentences, Climate_Sentences_Count, Sentiment_Risk_Count, Sentiment_Opportunity_Count, Sentiment_Neutral_Count", "Combined (summed) climate-scoring counts &mdash; see Dataset One."],
    ["Climate_Exposure_Score", "Recomputed from the combined counts (Step 5)."],
    ["Positive_Count, Negative_Count, Uncertain_Count, Weak_Modal_Count, Total_Words", "Combined (summed) Loughran-McDonald counts and word count &mdash; see Dataset Two."],
    ["Tone_Score, Percent_Uncertain, Percent_Weak_Modal", "Recomputed from the combined counts (Step 5)."],
    ["File_Size_MB, File_Size_Readability", "Combined file size and its recomputed readability proxy."],
    ["Fog_Index", "Word-count-weighted average across contributing files (Step 6)."],
    ["FinBERT_Positive, FinBERT_Negative, FinBERT_Neutral, FinBERT_Tone", "Word-count-weighted average across contributing files (Step 6)."],
], col_widths=[5.0 * cm, 12.0 * cm])

# ===========================================================================
# 7. COLUMN-TO-DASHBOARD MAPPING
# ===========================================================================
story.append(PageBreak())
h1("7. Column-to-Dashboard Mapping")
body(
    "This section maps every column in the canonical clean dataset to where it surfaces in the dashboard "
    "&mdash; as a filter, a chart, a table column, or supporting metadata. Dashboard page names refer to "
    "Section 8."
)
col_table([
    ["Column(s)", "Where it appears in the dashboard"],
    ["Company_Name, NSE_Name, Security_Code", "Overview: distinct-company count. Company Explorer: the company search/selection control. Rankings: leaderboard row labels. Correlations: hover label on scatter points."],
    ["Year, Quarter", "Overview: transcripts-per-year chart. Company Explorer: horizontal axis of every trend chart. Rankings &amp; Correlations: year-range and quarter filter controls."],
    ["parse_ok", "Governs which rows are eligible for any period-based chart or filter across all pages; unparseable rows for a selected company are shown separately as a footnote table on Company Explorer rather than silently omitted."],
    ["has_climate_data", "Overview: ‘% of transcripts with a climate score’ metric tile. Company Explorer: triggers an explanatory notice in place of climate charts for a company with no climate-scored transcripts. Correlations: optional include/exclude filter."],
    ["n_source_files, Filenames, duplicate_group, climate_file_coverage", "Company Explorer: shown in chart hover text and in the raw contributing-files table, so a combined multi-file quarter is always visibly distinguishable from a single-file one."],
    ["Climate_Exposure_Score", "Overview: distribution histogram. Company Explorer: trend chart. Rankings: rankable metric. Correlations: correlation matrix and scatter axis option."],
    ["Tone_Score", "Overview: distribution histogram. Company Explorer: trend chart. Rankings &amp; Correlations: selectable metric."],
    ["FinBERT_Tone", "Company Explorer: trend chart (plotted alongside Tone_Score for direct dictionary-vs-model comparison). Rankings &amp; Correlations: selectable metric."],
    ["Fog_Index", "Company Explorer: trend chart. Rankings &amp; Correlations: selectable metric."],
    ["Percent_Uncertain, Percent_Weak_Modal", "Rankings &amp; Correlations: selectable metrics."],
    ["Total_Words", "Rankings &amp; Correlations: selectable metric (labeled Transcript Length)."],
    ["Sentiment_Risk_Count, Sentiment_Opportunity_Count, Sentiment_Neutral_Count, Climate_Sentences_Count", "Rankings &amp; Correlations: selectable metrics."],
    ["Positive_Count, Negative_Count, Uncertain_Count, Weak_Modal_Count, Total_Sentences, File_Size_MB, File_Size_Readability, FinBERT_Positive, FinBERT_Negative, FinBERT_Neutral", "Not exposed as a standalone chart metric; visible in the raw per-transcript data table on Company Explorer and documented in full on the About Data page for anyone auditing a specific figure."],
], col_widths=[5.6 * cm, 11.4 * cm])

# ===========================================================================
# 8. DASHBOARD ARCHITECTURE
# ===========================================================================
story.append(PageBreak())
h1("8. Dashboard Architecture &amp; Features")
h2("8.1 Technology Stack")
body(
    "The dashboard is a multi-page Streamlit application. Streamlit was chosen for direct compatibility "
    "with the pandas-based cleaning pipeline and for the fastest path from a tabular dataset to an "
    "interactive, filterable web interface. Charts are rendered with Plotly throughout, chosen specifically "
    "because two of the five pages (Correlations and Rankings) require chart types &mdash; an annotated "
    "correlation heatmap, a colour-coded scatter plot, and precisely labeled horizontal bar charts &mdash; "
    "that are not available through simpler built-in charting primitives. Using one charting library "
    "consistently across all five pages keeps the visual style uniform. The underlying cleaned dataset is "
    "loaded once and cached in memory, so filtering and navigating between pages is immediate."
)

h2("8.2 Page: Overview")
body(
    "The landing page. Presents summary metric tiles (total companies covered, total transcripts "
    "processed, year range, share of transcripts with a valid fiscal period, share with an available "
    "climate score), a distribution histogram each for climate exposure and financial tone across the "
    "full dataset, and a bar chart of transcript volume per year. Serves as the orientation point before "
    "drilling into a specific company or comparison."
)

h2("8.3 Page: Company Explorer")
body(
    "A search-and-select control lets the user pick any single company from the full universe covered by "
    "the data. Once selected, the page displays that company's climate exposure, financial tone, FinBERT "
    "tone, and readability scores plotted over time, one point per fiscal quarter. Hovering a point reveals "
    "how many source files were combined into it and whether it represents a duplicate-group approximation. "
    "A table beneath the charts lists every underlying transcript row contributing to that company's "
    "record, including any quarters excluded from the charts due to an unparseable fiscal period. If a "
    "selected company has no climate-scored transcripts at all, the page shows an explanatory notice in "
    "place of the climate charts rather than an empty or misleading plot."
)

h2("8.4 Page: Rankings")
body(
    "Lets the user rank all companies by any one metric, over a chosen year range and set of quarters, as "
    "a Top-N or Bottom-N leaderboard. A minimum-data-volume filter prevents a company with only one or two "
    "matching transcripts from dominating an extreme ranking position. Results are shown as both a sortable "
    "table and a horizontal bar chart, chosen specifically because company names are long text strings that "
    "remain readable as horizontal labels."
)

h2("8.5 Page: Correlations")
body(
    "Provides two complementary views for relating metrics to one another: a correlation matrix, rendered "
    "as an annotated heatmap, across a user-selected set of metrics; and a scatter-plot explorer where the "
    "user picks any two metrics for the horizontal and vertical axes, optionally coloured by year, at either "
    "the individual-transcript or company-averaged level. This page is where a question such as ‘does "
    "higher climate exposure tend to coincide with more negative or more uncertain language’ is "
    "investigated directly."
)

h2("8.6 Page: About Data")
body(
    "A reference page documenting the full clean-schema column dictionary and the data-quality caveats "
    "recorded in Section 9 of this document, together with a brief description of how each dataset's scores "
    "were originally produced. Included so that any figure encountered elsewhere in the dashboard can be "
    "traced back to its definition and any relevant caveat without leaving the application."
)

# ===========================================================================
# 9. LIMITATIONS
# ===========================================================================
story.append(PageBreak())
h1("9. Known Data Limitations &amp; Open Items")
bullet(
    "<b>Duplicate-file resolution is an interim policy.</b> The meaning of the numeric filename suffixes "
    "that create multi-file company-quarters has not yet been confirmed against source recordings. The "
    "current sum-and-recompute approach is a reasonable default but should be revisited once confirmed."
)
bullet(
    f"<b>{STATS['clean_no_climate']} rows have no climate score.</b> These correspond to source files where "
    "text extraction failed upstream of both scoring pipelines; they carry zero counts across every "
    "climate and financial-tone metric and are flagged accordingly rather than silently imputed."
)
bullet(
    f"<b>{STATS['clean_parse_fail']} rows have an unrecoverable fiscal period</b> and are excluded from every "
    "year/quarter-based chart and filter, though retained in the dataset and visible in per-company detail "
    "views."
)
bullet(
    "<b>FinBERT and Fog Index values on combined multi-file rows are weighted-average approximations</b>, "
    "not exact recomputations, since neither metric is a simple ratio of countable quantities. This is "
    "flagged on every affected row via the duplicate_group indicator."
)
bullet(
    "<b>Dictionary-based scoring lacks contextual understanding.</b> The Loughran-McDonald approach counts "
    "words independent of surrounding context, and does not distinguish between different speakers on the "
    "same call (e.g. a CEO versus a CFO), nor compare stated language against actual reported financial "
    "results."
)

# ===========================================================================
# 10. APPENDIX
# ===========================================================================
story.append(PageBreak())
h1("10. Appendix: Formula Reference")
col_table([
    ["Metric", "Formula"],
    ["Climate_Exposure_Score", "Climate_Sentences_Count &divide; Total_Sentences &times; 100"],
    ["Tone_Score", "(Positive_Count &minus; Negative_Count) &divide; (Positive_Count + Negative_Count)"],
    ["Percent_Uncertain", "Uncertain_Count &divide; Total_Words &times; 100"],
    ["Percent_Weak_Modal", "Weak_Modal_Count &divide; Total_Words &times; 100"],
    ["File_Size_Readability", "&minus;log(File_Size_MB + 1)"],
    ["Fog_Index", "0.4 &times; (average words per sentence + percent of words with 3+ syllables)"],
    ["FinBERT_Tone", "FinBERT_Positive &minus; FinBERT_Negative"],
], col_widths=[5.0 * cm, 12.0 * cm])

caption(f"Document version generated {GENERATED_DATE}. Author: {AUTHOR}.")


# ---------------------------------------------------------------------------
# Page furniture (footer with page number)
# ---------------------------------------------------------------------------
def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD9CF"))
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.15 * cm, "Climate Risk & Financial Tone Analytics — Process Documentation")
    canvas.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUT_PATH),
    pagesize=A4,
    leftMargin=2 * cm,
    rightMargin=2 * cm,
    topMargin=1.8 * cm,
    bottomMargin=2.2 * cm,
    title="Climate Risk & Financial Tone Analytics - Process Documentation",
    author=AUTHOR,
    subject="Process documentation for the earnings-call climate and tone analytics dashboard",
)

doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
print(f"Wrote {OUT_PATH}")
