# Residential Demand Flexibility and Energy Expenditure Share

Code for the data pipeline of *Residential Demand Flexibility and Energy Expenditure Share Are Misaligned Across U.S. Households*. The pipeline generates synthetic one-minute residential load profiles for U.S. households, estimates each household's upward and downward demand flexibility with a trained LSTM model, and matches flexibility with each household's energy expenditure share (electricity bill / income).

Figure-plotting scripts are not included in this repository.

## Pipeline

| Step | Script | Purpose | Main output |
|---|---|---|---|
| 1 | `src/DownloadCPS.py` | Download Current Population Survey (CPS) microdata | `raw-data/cps/*.dat` |
| 2 | `src/cleanATUS.py` | Clean American Time Use Survey (ATUS) activity and location records | `processed-data/atus/` |
| 3 | `src/cleanCPS.py` | Clean CPS household demographics and link them to ATUS | `processed-data/cps/processed-cps-2023.csv` |
| 4 | `src/main_allstate.py` (with `src/HEM/`) | Generate one-minute load profiles for 100 synthetic households in a state from NSRDB weather and CPS demographics | `output-data/main-<ST>/output-household-<id>.csv`, `output-cps-subset.csv` |
| 5 | `src/analysis_allstate.py` | Summarise household load profiles by demographic group | `output-data/main-<ST>/analysis-*.csv` |
| 6 | `Flexibility_Envelope_Code/1Get_flexibility_bound_synthetic_state_output.py` (summer, by month)<br>`Flexibility_Envelope_Code/Get_flexibility_bound_synthetic_state_output.py` (winter) | Estimate upward and downward flexibility envelopes with the trained LSTM models (`*.keras`) | `Output_lower_bound_<ST>_<month>.csv`, `Output_upper_bound_<ST>_<month>.csv` |
| 7 | `Flexibility_Envelope_Code/Flexibility-Affordability/fle-aff csv generation.py` | Match July household flexibility with electricity cost, income and energy expenditure share by household ID | `Flex_Affordability_Matched_<ST>_July.csv` |

`src/HEM/` is the household energy model used in step 4 (HVAC, water heater, occupancy, lighting, cold and direct appliances).

## Data

Input data are not stored in this repository.

- **Weather:** National Solar Radiation Database (NSRDB), 2023, five-minute resolution, capital city of each state. Files are expected as `raw-data/nsrdb/<City>-<st>-2023-5-min-nsrdb.csv`.
- **Demographics:** CPS monthly microdata and record layouts (`raw-data/cps/`).
- **Activity patterns:** ATUS microdata (`raw-data/atus/`).
- **Electricity rates:** OpenEI Utility Rate Database (URDB), time-of-use rates for each state.

The scripts in `src/` resolve data paths relative to the repository root (`../raw-data`, `../processed-data`, `../output-data`). Scripts in `Flexibility_Envelope_Code/` contain absolute paths at the top of each file; edit them to point to your local data folders before running. The state to process is set near the top of `main_allstate.py` (`state = ...`) and in the state list of the flexibility scripts.

## Requirements

Python 3.11. Install dependencies with

```
pip install -r requirements.txt
```

## Citation

If you use this code, please cite the accompanying paper.
