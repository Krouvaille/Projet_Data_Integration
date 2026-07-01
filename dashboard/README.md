# Bronze Explorer dashboard

A Streamlit app that previews the four BAAC 2024 Bronze tables and visualizes the
data-quality findings from `notebooks/Road_Safety_Open_Data.ipynb`.

## Run

From the project root:

```bash
uv run streamlit run dashboard/app.py
```

## Layout

- `app.py` — home page (overview + row/column counts per table).
- `pages/1_Table_Explorer.py` — filter, sort and inspect one Bronze table at a time.
- `pages/2_Data_Quality_Report.py` — missing values, duplicates, referential integrity,
  grain, value ranges, distributions, domain anomalies, and ydata-profiling alerts.
- `lib/data.py` — cached CSV loading (`@st.cache_data`) and the table registry.
- `lib/profiling.py` — pure profiling functions lifted from the notebook (no Streamlit,
  so they stay testable and reusable).

The profiling functions reproduce the notebook's numbers exactly (2 `lieux` duplicates,
`adr` 4.2% missing, 28.8% multi-row `lieux`, 3,347 points outside the metropolitan box,
50 `#VALEURMULTI` rows in `lieux.nbv`, etc.).
