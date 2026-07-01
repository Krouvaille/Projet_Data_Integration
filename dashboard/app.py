"""BAAC 2024 road-safety Bronze-layer dashboard (home page).

Run from the project root:

    uv run streamlit run dashboard/app.py

Two pages (see the sidebar): a Table Explorer for interactive previews of the
four Bronze tables, and a Data Quality Report visualizing the profiling findings
from ``notebooks/Road_Safety_Open_Data.ipynb``.
"""

import streamlit as st

from lib.data import DATA_DIR, TABLES, load_all, missing_files

st.set_page_config(page_title="BAAC 2024 — Bronze Explorer", page_icon="🚦", layout="wide")

st.title("🚦 Road Safety Open Data 2024")
st.caption("BAAC *accidents corporels* 2024 · Medallion Bronze layer explorer")

# --- Readiness: fail clearly if the Bronze CSVs are not where we expect -------
missing = missing_files()
if missing:
    st.error(
        f"Missing Bronze CSV(s) under `{DATA_DIR}`: {', '.join(missing)}.\n\n"
        "Run the app from the project root so `data/` resolves correctly."
    )
    st.stop()

tables = load_all()

st.markdown(
    "Four semicolon-separated CSVs from data.gouv.fr, linked by the accident id "
    "`Num_Acc`. This dashboard previews the raw tables and surfaces the data-quality "
    "findings computed in the profiling notebook."
)

# --- Corpus at a glance -------------------------------------------------------
k = st.columns(4)
k[0].metric("Accidents", f"{len(tables['caract']):,}")
k[1].metric("Road segments", f"{len(tables['lieux']):,}")
k[2].metric("People", f"{len(tables['usagers']):,}")
k[3].metric("Vehicles", f"{len(tables['vehicules']):,}")

st.divider()

# --- The four Bronze tables as cards -----------------------------------------
st.subheader("The four Bronze tables")
cols = st.columns(4)
for col, (name, (_, grain, desc)) in zip(cols, TABLES.items()):
    df = tables[name]
    with col.container(border=True):
        st.markdown(f"**`{name}`**")
        st.metric("rows", f"{len(df):,}", f"{df.shape[1]} columns", delta_color="off")
        st.caption(f"Grain: {grain}.")
        st.caption(desc)

st.divider()

# --- Where to go next ---------------------------------------------------------
st.subheader("Explore")
nav = st.columns(2)
with nav[0].container(border=True):
    st.markdown("#### 🔎 Table Explorer")
    st.caption("Filter, sort and inspect each Bronze table interactively.")
    st.page_link("pages/1_Table_Explorer.py", label="Open Table Explorer", icon="🔎")
with nav[1].container(border=True):
    st.markdown("#### 📊 Data Quality Report")
    st.caption("Missing values, duplicates, integrity, ranges and anomalies — as charts.")
    st.page_link("pages/2_Data_Quality_Report.py", label="Open Data Quality Report", icon="📊")
