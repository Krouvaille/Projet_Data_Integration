"""Data Quality Report: visualizes the profiling findings from the notebook."""

import plotly.express as px
import streamlit as st

from lib.data import DATA_DIR, TABLES, load_all, missing_files
from lib.profiling import (
    age_check,
    coordinate_check,
    domain_violations,
    duplicate_count,
    grain_summary,
    missing_report,
    numeric_series,
    referential_integrity,
)

st.set_page_config(page_title="Data Quality Report", page_icon="📊", layout="wide")
st.title("📊 Data Quality Report")

if missing_files():
    st.error(f"Bronze CSVs not found under `{DATA_DIR}`. Run the app from the project root.")
    st.stop()

tables = load_all()


@st.cache_data(show_spinner="Computing ydata-profiling alerts...")
def ydata_alerts(name: str) -> list[str]:
    """Column-level alerts from ydata-profiling, as in the notebook."""
    from ydata_profiling import ProfileReport

    report = ProfileReport(tables[name], title=name, minimal=True, progress_bar=False)
    return [str(a) for a in report.get_description().alerts]


# --- Missing values -----------------------------------------------------------
st.header("Missing values")
st.markdown(
    "Counting both `NaN` and the BAAC `-1` sentinel (stripped of leading spaces). "
    "Large percentages mostly reflect conditional applicability (e.g. pedestrian-only "
    "fields), not quality problems."
)
tabs = st.tabs(list(TABLES))
for tab, name in zip(tabs, TABLES):
    with tab:
        rep = missing_report(tables[name]).reset_index(names="column")
        if rep.empty:
            st.success("No missing values.")
            continue
        fig = px.bar(
            rep, x="pct", y="column", orientation="h",
            labels={"pct": "% missing", "column": ""}, text="pct",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(240, 26 * len(rep)))
        st.plotly_chart(fig, width="stretch")

# --- Duplicates ---------------------------------------------------------------
st.header("Duplicate rows")
dup_cols = st.columns(4)
for col, name in zip(dup_cols, TABLES):
    col.metric(name, f"{duplicate_count(tables[name]):,}")
st.caption(
    "The 2 `lieux` duplicates are accidents 202400012279 and 202400044389. "
    "`lieux`'s road-segment grain means many accidents legitimately have several rows "
    "(that is not duplication)."
)

# --- Referential integrity & grain -------------------------------------------
st.header("Referential integrity & grain")
c1, c2 = st.columns([1.2, 1])
with c1:
    st.dataframe(referential_integrity(tables), width="stretch", hide_index=True)
    st.caption("No orphans in either direction — referential integrity is complete.")
with c2:
    grain = grain_summary(tables)
    st.metric("lieux multi-row accidents", f"{grain['lieux multi-row accidents']:,}",
              f"{grain['lieux multi-row pct']}% of accidents")
    st.metric("Usagers per accident", grain["usagers per accident"])
    st.metric("Vehicules per accident", grain["vehicules per accident"])
    st.metric("Usagers per vehicule", grain["usagers per vehicule"])

# --- Ranges: coordinates & ages ----------------------------------------------
st.header("Value ranges")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Coordinates (caract)")
    coord = coordinate_check(tables["caract"])
    st.write(
        f"Latitude {coord['lat_min']} to {coord['lat_max']}, "
        f"longitude {coord['long_min']} to {coord['long_max']}."
    )
    st.metric("Outside metropolitan box", f"{coord['outside_metro']:,}",
              f"{coord['outside_metro_pct']}%")
    st.caption(
        f"{coord['outside_but_overseas']:,} of those are overseas departments "
        "(valid data), so do not filter to metropolitan France only."
    )
with c2:
    st.subheader("Ages (usagers)")
    age = age_check(tables["usagers"])
    st.write(f"Ages range from {age['age_min']} to {age['age_max']}.")
    st.metric("Negative ages", age["negative_ages"])

# --- Distributions ------------------------------------------------------------
st.header("Distributions")
st.caption("Object columns (decimal-comma / space-separated) are parsed for charting; "
           "`-1` sentinels and `#VALEURMULTI` drop out as NaN.")
dc1, dc2 = st.columns(2)
name = dc1.selectbox("Table", list(TABLES), key="dist_table")
col = dc2.selectbox("Column", list(tables[name].columns), key="dist_col")
values = numeric_series(tables[name], col)
if values.empty:
    st.info("No numeric values to plot for this column.")
else:
    fig = px.histogram(values, nbins=40, labels={"value": col})
    fig.update_layout(showlegend=False, xaxis_title=col, yaxis_title="rows", height=360)
    st.plotly_chart(fig, width="stretch")

# --- Domain anomalies ---------------------------------------------------------
st.header("Domain validity & anomalies")
st.dataframe(domain_violations(tables), width="stretch", hide_index=True)
st.caption("All coded fields respect their official domains except `lieux.nbv`, which "
           "carries 50 rows of the literal Excel-error text `#VALEURMULTI`.")

# --- ydata-profiling alerts (opt-in, heavier) --------------------------------
st.header("Automated alerts (ydata-profiling)")
if st.checkbox("Compute ydata-profiling alerts"):
    for name in TABLES:
        st.subheader(name)
        alerts = ydata_alerts(name)
        if alerts:
            for a in alerts:
                st.write("•", a)
        else:
            st.success("No alerts.")
