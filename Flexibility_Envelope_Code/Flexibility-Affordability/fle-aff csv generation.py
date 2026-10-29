# -*- coding: utf-8 -*-
"""
Match state-level Flexibility (July) with Energy Affordability (Energy Burden)
----------------------------------------------------------------------------
Inputs:
1) Flexibility folder:
   F:\E PhD\Heat map(2025)\state_flexibility_July_csvs\
   Each file: Flexibility_{ST}_July.csv
   Columns (with header row): idx, household_id, flex_UL, flex_UO, flex_OL

2) Affordability folder:
   F:\E PhD\Heat map(2025)\EA_RemoveOutliers\
   Each file: Energy_Burden_{ST}.csv
   FIRST ROW is TEXT (not header)
   Then columns: household ID, cost, income, burden

Task:
- For each state, match by household ID
- Output one CSV per state with:
    Row 1: text line
    Col1: idx (0..99)
    Col2: household_id
    Col3: flex_UL
    Col4: flex_UO (upward)
    Col5: flex_OL (downward)
    Col6: cost
    Col7: income
    Col8: burden
- Save to new folder under BASE:
    F:\E PhD\Heat map(2025)\Flexibility_Affordability_Matched_July\

Also writes a run log for quick debugging.
"""

import os
import numpy as np
import pandas as pd

BASE = r"F:\E PhD\Heat map(2025)"
FLEX_DIR = os.path.join(BASE, "state_flexibility_July_csvs")
EA_DIR = os.path.join(BASE, "EA_RemoveOutliers")

OUT_DIR = os.path.join(BASE, "Flexibility_Affordability_Matched_July")
os.makedirs(OUT_DIR, exist_ok=True)

STATES_50 = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
]

def read_flex_csv(path: str) -> pd.DataFrame:
    """Flex CSV already has headers."""
    df = pd.read_csv(path)
    # normalize
    df.columns = [c.strip().lower() for c in df.columns]
    rename_map = {
        "household": "household_id",
        "householdid": "household_id",
        "household_id": "household_id",
        "idx": "idx",
        "flex_ul": "flex_ul",
        "flex_uo": "flex_uo",
        "flex_ol": "flex_ol",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    needed = ["idx", "household_id", "flex_ul", "flex_uo", "flex_ol"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Flex file missing columns: {missing}")
    df["idx"] = pd.to_numeric(df["idx"], errors="coerce")
    df["household_id"] = pd.to_numeric(df["household_id"], errors="coerce")
    return df[needed]

def read_ea_csv_skip_text_firstrow(path: str) -> pd.DataFrame:
    """
    EA csv: first row is TEXT.
    Then data rows have: household_id, cost, income, burden (no header).
    """
    # skip first row text
    df = pd.read_csv(path, header=None, skiprows=1)
    if df.shape[1] < 4:
        raise ValueError(f"EA file has <4 columns after skipping first row: {path}")
    df = df.iloc[:, :4].copy()
    df.columns = ["household_id", "cost", "income", "burden"]
    # numeric conversion
    for c in ["household_id", "cost", "income", "burden"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # drop rows without household_id
    df = df.dropna(subset=["household_id"])
    return df

def write_with_text_firstrow(df: pd.DataFrame, out_path: str, text_line: str):
    """Write first row as text, then header+data."""
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text_line.rstrip("\n") + "\n")
    df.to_csv(out_path, mode="a", index=False, encoding="utf-8-sig")

log_rows = []

for st in STATES_50:
    try:
        flex_path = os.path.join(FLEX_DIR, f"Flexibility_{st}_July.csv")
        ea_path   = os.path.join(EA_DIR,   f"Energy_Burden_{st}.csv")
        if not os.path.exists(flex_path):
            raise FileNotFoundError(f"Missing flex file: {flex_path}")
        if not os.path.exists(ea_path):
            raise FileNotFoundError(f"Missing EA file: {ea_path}")

        flex = read_flex_csv(flex_path)
        ea = read_ea_csv_skip_text_firstrow(ea_path)

        # Match by household_id (left join: keep 0..99 rows)
        merged = flex.merge(ea, on="household_id", how="left")

        # Final column order as you requested
        merged = merged.rename(columns={
            "flex_ul": "UL_flexibility",
            "flex_uo": "Upward_flexibility",
            "flex_ol": "Downward_flexibility",
            "burden": "Burden"
        })

        out_cols = [
            "idx",
            "household_id",
            "UL_flexibility",
            "Upward_flexibility",
            "Downward_flexibility",
            "cost",
            "income",
            "Burden"
        ]
        merged = merged[out_cols].copy()

        # Ensure idx is 0..99 if present
        merged["idx"] = pd.to_numeric(merged["idx"], errors="coerce").astype("Int64")

        # Optional: count matched rows
        n_total = len(merged)
        n_matched = int(merged["cost"].notna().sum())

        out_path = os.path.join(OUT_DIR, f"Flex_Affordability_Matched_{st}_July.csv")
        text_line = (f"Matched Flexibility (July) + Energy Affordability (Energy Burden) for {st}. "
                     f"Matched households: {n_matched}/{n_total}.")
        write_with_text_firstrow(merged, out_path, text_line)

        log_rows.append({
            "state": st,
            "status": "OK",
            "rows_out": n_total,
            "matched_rows": n_matched,
            "out_path": out_path
        })
        print(f"[{st}] OK  matched {n_matched}/{n_total} -> {out_path}")

    except Exception as e:
        log_rows.append({
            "state": st,
            "status": "FAIL",
            "rows_out": 0,
            "matched_rows": 0,
            "out_path": "",
            "error": str(e)
        })
        print(f"[{st}] FAIL: {e}")

# Save run log
log_df = pd.DataFrame(log_rows)
log_path = os.path.join(OUT_DIR, "run_log_match_flex_affordability.csv")
log_df.to_csv(log_path, index=False, encoding="utf-8-sig")

print("\nDone.")
print("Outputs folder:")
print(" ", OUT_DIR)
print("Run log:")
print(" ", log_path)
