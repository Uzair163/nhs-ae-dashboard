# NHS A&E Performance Dashboard (Streamlit)

## Run locally
```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501. The four pages (National Performance, 12-Hour Wait Crisis, Trust Comparison, Winter Forecast) appear in the sidebar automatically — that's Streamlit's built-in multipage behavior based on the `pages/` folder, no extra config needed.

## A note on how this was built
Streamlit and pandas weren't available in the sandbox this was developed in, and there was no network access to install them. So the data logic (`data.py`) was written and fully tested with plain pandas — every number in it was cross-checked against figures validated earlier in the project (e.g. Dec 2022 = 67.2% national / 10.55% 12-hour waits, 19 persistent bottom-quartile Trusts). The Streamlit UI code on top of it was checked with a fake `streamlit` stub (`_dev_smoke_test.py`) that catches real Python errors — wrong column names, broken calls — but can't verify that anything actually **looks** right.

**This means the first local run is genuinely the first time this has rendered.** If something looks wrong (a chart empty, a layout off, a Streamlit API call that's changed since I last knew it), that's expected as a possibility, not a sign something is fundamentally broken — tell me what you see and I'll fix it fast, since the underlying data is already solid.

`_dev_smoke_test.py` isn't part of the app — it's the stub-testing script described above, kept for reference/re-running after future changes. Fine to delete before deploying, or leave it, it won't affect the deployed app.

## Deploying online (Streamlit Community Cloud — free)
1. Push this whole `nhs_project` folder to a GitHub repo (public or private).
2. Go to share.streamlit.io, sign in with GitHub, click "New app".
3. Point it at the repo, set the main file path to `app/app.py`.
4. Deploy. It rebuilds automatically on every push to the branch you select.

The app reads data from `../output/powerbi_model/*.csv` relative to `app/`, so those four CSVs need to stay in the repo alongside the app code — they're small (a few MB total), no external database or storage needed.

## Regenerating the data
If you re-run the RAP pipeline (`src/ingest.py` → `src/build_panel.py` → `src/forecast.py`) with new raw data, re-run the Power BI model-export step that produced `output/powerbi_model/*.csv` (see docs/powerbi_measures.md for the schema) and the Streamlit app picks up the new numbers automatically on next reload — no code changes needed.
