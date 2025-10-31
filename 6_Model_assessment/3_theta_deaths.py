import numpy as np
import pandas as pd
from tqdm import tqdm
import json
import ast


file = open("comparison_gtap_new/Total_pop_gtap.json", "r")
Total_pop_gtap = file.read()
Total_pop_gtap = json.loads(Total_pop_gtap)
Countries_list=list(Total_pop_gtap.keys())

scaled_Total_pop_gtap = {}
for k, v in Total_pop_gtap.items():
    try:
        scaled_Total_pop_gtap[k] = float(v) / 100000.0
    except (TypeError, ValueError):
        # keep original if not numeric
        scaled_Total_pop_gtap[k] = v

# (Optional) overwrite the original variable
Total_pop_gtap = scaled_Total_pop_gtap

fraction1 = pd.read_csv('comparison_gtap/theta_draws.csv',index_col=0)
print(np.shape(fraction1))


# production based concentrations
#consumption_concentration_gtap = pd.read_csv('comparison_gtap_new/concentration_by_sectors_gtap.csv',index_col=0)
df_list = []

for country in tqdm(Countries_list, desc="Reading and renaming country CSVs"):
    path = f"comparison_gtap_new/Production_concentrations/{country}.csv"

    # Read the CSV with the first column as index
    df = pd.read_csv(path, header=0, index_col=0)
    
    # Prefix all column names with the country code
    df.columns = [f"{country}_{col}" for col in df.columns]
    
    # Append to list
    df_list.append(df)

# Concatenate along columns (axis=1)
consumption_concentration_gtap = pd.concat(df_list, axis=1)

'''

# consumption based concentrations
consumption_concentration_gtap = pd.read_csv('comparison_gtap_new/concentration_matrix_gtap.csv',header=None)
consumption_concentration_gtap.columns=Countries
'''
consumption_concentration_gtap = consumption_concentration_gtap.astype(float)

print(f"Rows in theta_draws.csv: {fraction1.shape[0]}")
print(f"Rows in concentration_matrix_gtap.csv: {consumption_concentration_gtap.shape[0]}")


def parse_dict_with_np(val):
    try:
        if isinstance(val, dict):
            return val
        val = val.replace("np.float64(", "").replace(")", "")
        return ast.literal_eval(val)
    except Exception:
        return {}


theta_cols = [col for col in fraction1.columns if col.startswith("mort_per_con_theta_")]

for col in tqdm(theta_cols):
    fraction1[col] = fraction1[col].apply(parse_dict_with_np)

# ---- Inputs expected (already prepared) ----
# fraction1: has mort_per_con_theta_* dict-columns (one per θ draw), same row order as consumption_concentration_gtap
# consumption_concentration_gtap: rows=grid cells, columns=consumer countries (concentration contributed by that consumer)
# Countries: list of consumer countries (columns to use from consumption_concentration_gtap)
# Total_pop_gtap: dict {producer_country: population}  <-- we want deaths, so we multiply by this

# 0) Consumers
Consumers = list(consumption_concentration_gtap.columns)

# 1) Draw columns and producer universe (union of keys seen in dicts)
draw_cols = [c for c in fraction1.columns if c.startswith("mort_per_con_theta_")]
if not draw_cols:
    raise ValueError("No mort_per_con_theta_* columns found in fraction1.")

producer_keys = set()
for col in draw_cols:
    for d in fraction1[col].values:
        if isinstance(d, dict):
            producer_keys.update(d.keys())
Producers = sorted(producer_keys)

prod_index = {p: j for j, p in enumerate(Producers)}

# 2) W: consumer concentration matrix (N x C)
W = consumption_concentration_gtap[Consumers].to_numpy(dtype=float, copy=True)
WT = W.T
N, C = W.shape
P = len(Producers)
D = len(draw_cols)

# 3) Producer populations aligned to Producers
Pvec = np.array([Total_pop_gtap.get(p, 0.0) for p in Producers], dtype=float)
missing_pop = [p for p in Producers if p not in Total_pop_gtap]
if missing_pop:
    print("[WARN] Missing producer population for:", missing_pop, "(treated as 0)")

def dictcol_to_matrix(dict_series: pd.Series, col_index_map: dict[str, int], n_rows: int, n_cols: int) -> np.ndarray:
    M = np.zeros((n_rows, n_cols), dtype=float)
    for i, d in enumerate(dict_series.values):
        if not d:
            continue
        for k, v in d.items():
            j = col_index_map.get(k)
            if j is not None:
                M[i, j] = float(v)
    return M

# 4) Aggregate all draws → deaths * population only
Totals_draws_pop = np.empty((D, C, P), dtype=float)

for d_idx, col in enumerate(tqdm(draw_cols, desc="Aggregating θ draws (deaths only)")):
    M = dictcol_to_matrix(fraction1[col], prod_index, N, P)   # (N x P)
    Totals = WT @ M                                           # (C x P) = deaths (unscaled)
    Totals_pop = Totals * Pvec[None, :]                       # (C x P) = deaths × producer population
    Totals_draws_pop[d_idx] = Totals_pop

# 5) Summaries: median & 95% UI (deaths only)
med = np.median(Totals_draws_pop, axis=0)
lo  = np.percentile(Totals_draws_pop,  2.5, axis=0)
hi  = np.percentile(Totals_draws_pop, 97.5, axis=0)

global_draws_pop = Totals_draws_pop.sum(axis=(1, 2))
global_summary_pop = {
    "median": float(np.median(global_draws_pop)),
    "low95": float(np.percentile(global_draws_pop, 2.5)),
    "high95": float(np.percentile(global_draws_pop, 97.5)),
    "draws_used": int(D),
}

# 6) Tidy pair table (deaths only)
rows = []
for ic, cons in enumerate(Consumers):
    for jp, prod in enumerate(Producers):
        rows.append({
            "Consumer": cons,
            "Producer": prod,
            "Deaths_median": med[ic, jp],
            "Deaths_low95":  lo[ic, jp],
            "Deaths_high95": hi[ic, jp],
        })
df_pairs_deaths = pd.DataFrame(rows).sort_values(
    ["Consumer", "Deaths_median"], ascending=[True, False], ignore_index=True
)

# 7) Save (only deaths)
df_pairs_deaths.to_csv("comparison_gtap_new/mortality_pairs_deaths_popscaled_production.csv", index=False)
pd.DataFrame([global_summary_pop]).to_csv("comparison_gtap_new/global_mortality_deaths_popscaled_global_production.csv", index=False)

# Full cube if you want to reuse later (optional)
np.savez_compressed(
    "totals_draws_consumer_by_producer_deaths_popscaled_production.npz",
    Totals_draws_pop=Totals_draws_pop,
    Consumers=np.array(Consumers, dtype=object),
    Producers=np.array(Producers, dtype=object),
    draw_cols=np.array(draw_cols, dtype=object),
)

print("Global deaths (GEMM θ uncertainty): "
      f"{global_summary_pop['median']:,.0f} "
      f"[{global_summary_pop['low95']:,.0f}–{global_summary_pop['high95']:,.0f}]")
