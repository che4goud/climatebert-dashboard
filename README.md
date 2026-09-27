# Climate Risk & Financial Tone Analytics Dashboard

A Streamlit dashboard for exploring climate-risk exposure and financial tone in quarterly
earnings-call transcripts of BSE-listed companies.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Regenerate the cleaned dataset

```bash
python scripts/clean_data.py
pytest tests/test_clean_data.py
```

## Run the dashboard

```bash
streamlit run app/Home.py
```

## Regenerate the process documentation PDF

```bash
python scripts/generate_process_doc.py
```

See `PROJECT_LOG.md` for the running history of decisions and progress, and
`Process_Documentation.pdf` for the full write-up of both source datasets, the cleaning
pipeline, and the dashboard's features.
