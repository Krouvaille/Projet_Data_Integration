"""Table Explorer: interactive preview of one Bronze table at a time."""

import pandas as pd
import streamlit as st

from lib.data import DATA_DIR, TABLES, load_table, missing_files
from lib.profiling import dtypes_report

st.set_page_config(page_title="Table Explorer", page_icon="🔎", layout="wide")
st.title("🔎 Table Explorer")

if missing_files():
    st.error(f"Bronze CSVs not found under `{DATA_DIR}`. Run the app from the project root.")
    st.stop()

name = st.sidebar.selectbox(
    "Bronze table",
    list(TABLES),
    format_func=lambda n: f"{n}  ·  {TABLES[n][1]}",
)
_, grain, desc = TABLES[name]
df = load_table(name)

st.caption(f"**{name}** — grain: {grain}. {desc}")

c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", df.shape[1])
c3.metric("Exact duplicate rows", f"{int(df.duplicated().sum()):,}")

# --- Filtering on key columns -------------------------------------------------
st.sidebar.header("Filters")
filtered = df

acc = st.sidebar.text_input("Num_Acc contains", "").strip()
if acc:
    filtered = filtered[filtered["Num_Acc"].astype(str).str.contains(acc, na=False)]

# Generic per-column filter: categorical multiselect for low-cardinality columns,
# numeric range slider otherwise.
filter_cols = st.sidebar.multiselect(
    "Filter columns", [c for c in df.columns if c != "Num_Acc"]
)
for col in filter_cols:
    series = df[col]
    nunique = series.nunique(dropna=True)
    if pd.api.types.is_numeric_dtype(series) and nunique > 20:
        lo, hi = float(series.min()), float(series.max())
        if lo < hi:
            sel = st.sidebar.slider(f"{col} range", lo, hi, (lo, hi))
            filtered = filtered[filtered[col].between(*sel)]
    else:
        options = sorted(series.dropna().unique().tolist(), key=str)
        chosen = st.sidebar.multiselect(f"{col} values", options)
        if chosen:
            filtered = filtered[filtered[col].isin(chosen)]

st.markdown(f"**{len(filtered):,}** of {len(df):,} rows after filtering.")
st.dataframe(filtered, width="stretch", height=460)

with st.expander("Column dtypes"):
    st.dataframe(dtypes_report(df), width="stretch", hide_index=True)
