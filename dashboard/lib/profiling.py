"""Profiling computations lifted from ``notebooks/Road_Safety_Open_Data.ipynb``.

These are pure functions over the already-loaded Bronze frames. They only
detect and measure; nothing is persisted back onto the frames (any parsing,
like decimal-comma coordinates or ``-1``-as-missing, is a local throwaway
computation, exactly as in the notebook's Profiling stage).
"""

import pandas as pd

# Official code domains, as checked in the notebook (‑1 = "not specified", excluded).
DOMAINS = {
    "caract": {"atm": set(range(1, 10)), "col": set(range(1, 8))},
    "lieux": {"catr": {1, 2, 3, 4, 5, 6, 7, 9}},
    "usagers": {"grav": {1, 2, 3, 4}, "catu": {1, 2, 3}, "sexe": {1, 2}},
}


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Percent missing per column, counting NaN and the ``-1`` sentinel.

    Pandas already reads empty cells and ``N/A`` as NaN; BAAC additionally
    encodes "not specified" as ``-1`` (sometimes with a leading space in object
    columns), so we strip before comparing. Returns columns with >0% missing,
    sorted descending, with a ``pct`` and ``count`` column.
    """
    stripped = df.astype(str).replace(r"^\s+|\s+$", "", regex=True)
    missing = df.isna() | (stripped == "-1")
    count = missing.sum()
    pct = (missing.mean() * 100).round(1)
    out = pd.DataFrame({"count": count, "pct": pct})
    out = out[out["pct"] > 0].sort_values("pct", ascending=False)
    return out


def dtypes_report(df: pd.DataFrame) -> pd.DataFrame:
    """Column / inferred dtype table."""
    return pd.DataFrame({"column": df.columns, "dtype": df.dtypes.astype(str).values})


def duplicate_count(df: pd.DataFrame) -> int:
    """Number of exact duplicate rows."""
    return int(df.duplicated().sum())


def referential_integrity(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Orphan counts in both directions against ``caract`` accidents."""
    accidents = set(tables["caract"]["Num_Acc"])
    rows = []
    for name in ("lieux", "usagers", "vehicules"):
        others = set(tables[name]["Num_Acc"])
        rows.append(
            {
                "table": name,
                "orphan rows (no accident)": len(others - accidents),
                "accidents missing from table": len(accidents - others),
            }
        )
    return pd.DataFrame(rows)


def grain_summary(tables: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Grain / cardinality figures used to justify the star schema."""
    caract, lieux, usagers, vehicules = (
        tables["caract"],
        tables["lieux"],
        tables["usagers"],
        tables["vehicules"],
    )
    multi = int((lieux["Num_Acc"].value_counts() > 1).sum())
    return {
        "lieux multi-row accidents": multi,
        "lieux multi-row pct": round(multi / len(caract) * 100, 1),
        "usagers per accident": round(len(usagers) / len(caract), 2),
        "vehicules per accident": round(len(vehicules) / len(caract), 2),
        "usagers per vehicule": round(len(usagers) / vehicules["id_vehicule"].nunique(), 2),
        "usagers with orphan id_vehicule": len(
            set(usagers["id_vehicule"]) - set(vehicules["id_vehicule"])
        ),
    }


def coordinate_check(caract: pd.DataFrame) -> dict[str, float]:
    """Parse decimal-comma lat/long locally and locate points outside metro France."""
    lat = pd.to_numeric(caract["lat"].str.replace(",", ".", regex=False), errors="coerce")
    lon = pd.to_numeric(caract["long"].str.replace(",", ".", regex=False), errors="coerce")
    metro = lat.between(41, 52) & lon.between(-5.5, 10)
    overseas = caract["dep"].astype(str).str.startswith(("97", "98"))
    return {
        "lat_min": round(float(lat.min()), 2),
        "lat_max": round(float(lat.max()), 2),
        "long_min": round(float(lon.min()), 2),
        "long_max": round(float(lon.max()), 2),
        "outside_metro": int((~metro).sum()),
        "outside_metro_pct": round(float((~metro).mean()) * 100, 1),
        "outside_but_overseas": int((~metro & overseas).sum()),
    }


def age_check(usagers: pd.DataFrame) -> dict[str, int]:
    """Ages derived from ``an_nais`` (2024 reference year)."""
    age = 2024 - usagers["an_nais"]
    return {
        "age_min": int(age.min()),
        "age_max": int(age.max()),
        "negative_ages": int((age < 0).sum()),
    }


def domain_violations(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Coded values falling outside their official domain (``-1`` excluded)."""
    rows = []
    for table_name, cols in DOMAINS.items():
        df = tables[table_name]
        for col, allowed in cols.items():
            invalid = sorted(set(df[col].unique()) - allowed - {-1})
            rows.append(
                {
                    "table": table_name,
                    "column": col,
                    "invalid values": ", ".join(map(str, invalid)) if invalid else "none",
                }
            )
    # The one real anomaly: literal #VALEURMULTI text in lieux.nbv.
    valeurmulti = int((tables["lieux"]["nbv"].astype(str).str.strip() == "#VALEURMULTI").sum())
    rows.append(
        {
            "table": "lieux",
            "column": "nbv",
            "invalid values": f"{valeurmulti} rows of literal '#VALEURMULTI'" if valeurmulti else "none",
        }
    )
    return pd.DataFrame(rows)


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    """A column coerced to numeric for distribution charts.

    Handles the object columns the notebook flags: decimal-comma values and
    non-breaking-space thousands separators (``pr``/``pr1``). ``-1`` sentinels
    and ``#VALEURMULTI`` become NaN and drop out.
    """
    s = df[column]
    if s.dtype == object:
        s = (
            s.astype(str)
            .str.replace(" ", "", regex=False)  # non-breaking-space thousands sep
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        s = pd.to_numeric(s, errors="coerce")
    return pd.to_numeric(s, errors="coerce").replace(-1, pd.NA).dropna()
