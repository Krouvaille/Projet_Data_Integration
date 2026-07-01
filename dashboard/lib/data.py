"""Load and describe the four Bronze BAAC 2024 tables.

Ingestion here mirrors the notebook's Bronze stage: a bare ``pd.read_csv(sep=";")``
with no cleaning. Any parsing (decimal-comma coordinates, ``-1`` sentinels) belongs
to profiling and stays a local throwaway computation, never persisted back onto the
loaded frames.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# dashboard/lib/data.py -> project root is two levels up from this file's parent.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Table registry: name -> (csv filename, grain, one-line description).
TABLES = {
    "caract": ("caract-2024.csv", "one accident", "Date, time, lighting, location, weather, collision type."),
    "lieux": ("lieux-2024.csv", "one road segment", "Road category, geometry, surface, speed limit."),
    "usagers": ("usagers-2024.csv", "one person", "Role, injury severity, sex, birth year, safety equipment."),
    "vehicules": ("vehicules-2024.csv", "one vehicle", "Category, obstacle, impact point, maneuver."),
}


def missing_files() -> list[str]:
    """Names of registered tables whose CSV is not present under ``data/``."""
    return [name for name, (fn, *_) in TABLES.items() if not (DATA_DIR / fn).exists()]


@st.cache_data(show_spinner="Loading Bronze CSVs...")
def load_table(name: str) -> pd.DataFrame:
    """Read one Bronze CSV as-is (semicolon separated, no cleaning)."""
    filename = TABLES[name][0]
    return pd.read_csv(DATA_DIR / filename, sep=";")


@st.cache_data(show_spinner="Loading Bronze CSVs...")
def load_all() -> dict[str, pd.DataFrame]:
    """Load all four Bronze tables into a name -> DataFrame dict."""
    return {name: load_table(name) for name in TABLES}
